import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import Loader from '../Loader/Loader';
import { evaluateSystem } from '../../api';
import './EvaluatorTab.css';

const MRR_GREEN = 0.9, MRR_AMBER = 0.75;
const NDCG_GREEN = 0.9, NDCG_AMBER = 0.75;
const COVERAGE_GREEN = 90.0, COVERAGE_AMBER = 75.0;
const ANSWER_GREEN = 4.5, ANSWER_AMBER = 4.0;

const getColor = (value, metric) => {
  if (metric === 'mrr') return value >= MRR_GREEN ? 'green' : value >= MRR_AMBER ? 'orange' : 'red';
  if (metric === 'ndcg') return value >= NDCG_GREEN ? 'green' : value >= NDCG_AMBER ? 'orange' : 'red';
  if (metric === 'coverage') return value >= COVERAGE_GREEN ? 'green' : value >= COVERAGE_AMBER ? 'orange' : 'red';
  return value >= ANSWER_GREEN ? 'green' : value >= ANSWER_AMBER ? 'orange' : 'red';
};

const MetricCard = ({ label, value, metricType, isPercentage = false, scoreFormat = false }) => {
  const color = getColor(value, metricType);
  const displayValue = isPercentage ? `${value.toFixed(1)}%` : scoreFormat ? `${value.toFixed(2)}/5` : value.toFixed(4);
  
  return (
    <div className={`metric-card ${color}`}>
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${color}`}>{displayValue}</div>
    </div>
  );
};

const EvaluatorTab = () => {
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('gpt-4o-mini');
  const [topK, setTopK] = useState(5);
  const [usePinecone, setUsePinecone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleRunEvaluation = async () => {
    if (!file) {
      setError("Please upload a tests.jsonl file");
      return;
    }
    const topKNum = parseInt(topK);
    if (isNaN(topKNum) || topKNum <= 0 || topKNum > 20) {
      alert("Top K must be between 1 and 20.");
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);
    try {
      const vectorStore = usePinecone ? "pinecone" : "chroma";
      const res = await evaluateSystem(file, topKNum, vectorStore, model);
      
      // Calculate Averages
      let totalMrr = 0, totalNdcg = 0, totalCoverage = 0;
      let totalAcc = 0, totalComp = 0, totalRel = 0;
      const catMrr = {};
      const catAcc = {};
      
      const evals = res.results;
      evals.forEach(r => {
        totalMrr += r.retrieval.mrr;
        totalNdcg += r.retrieval.ndcg;
        totalCoverage += r.retrieval.keyword_coverage;
        totalAcc += r.answer_eval.accuracy;
        totalComp += r.answer_eval.completeness;
        totalRel += r.answer_eval.relevance;
        
        if (!catMrr[r.category]) catMrr[r.category] = [];
        if (!catAcc[r.category]) catAcc[r.category] = [];
        
        catMrr[r.category].push(r.retrieval.mrr);
        catAcc[r.category].push(r.answer_eval.accuracy);
      });
      
      const count = evals.length;
      const chartData = Object.keys(catMrr).map(cat => ({
        category: cat,
        mrr: catMrr[cat].reduce((a, b) => a + b, 0) / catMrr[cat].length,
        accuracy: catAcc[cat].reduce((a, b) => a + b, 0) / catAcc[cat].length
      }));

      setResults({
        count,
        mrr: totalMrr / count,
        ndcg: totalNdcg / count,
        coverage: totalCoverage / count,
        accuracy: totalAcc / count,
        completeness: totalComp / count,
        relevance: totalRel / count,
        chartData
      });
      
    } catch (err) {
      setError(`Evaluation failed: ${err.message}`);
    }
    setLoading(false);
  };

  return (
    <motion.div 
      className="evaluator-tab"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <div className="section controls-section">
        <h3>Evaluation Setup</h3>
        
        <div className="chat-container">
          <div className="input-group flex-1">
            <label>Upload Ground Truth (tests.jsonl)</label>
            <input type="file" accept=".jsonl" onChange={(e) => setFile(e.target.files[0])} />
          </div>
          
          <div className="input-group flex-none">
            <label>LLM Judge Model</label>
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4o">gpt-4o</option>
              <option value="gpt-4-turbo">gpt-4-turbo</option>
              <option value="gpt-4.1-nano">gpt-4.1-nano</option>
              <option value="gpt-5">gpt-5</option>
              <option value="gpt-5-turbo">gpt-5-turbo</option>
            </select>
          </div>
        </div>

        <div className="advanced-controls">
          <div className="input-group slider-group">
            <label>Top K Results (1-20)</label>
            <input 
              type="number" 
              min="1" 
              max="20" 
              value={topK} 
              onChange={(e) => setTopK(e.target.value)}
            />
          </div>
          
          <div className="input-group toggle-group">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <label className="switch">
                <input 
                  type="checkbox" 
                  checked={usePinecone} 
                  onChange={(e) => setUsePinecone(e.target.checked)} 
                />
                <span className="slider round"></span>
              </label>
              <label style={{ marginBottom: 0 }}>Use Pinecone Vector Store</label>
            </div>
          </div>
        </div>

        {error && <div className="status-box error">{error}</div>}

        <button className="submit-btn" onClick={handleRunEvaluation} disabled={loading || !file}>
          {loading ? <Loader text="Running Multithreaded Evaluation..." showTimer={true} /> : 'Run Evaluation'}
        </button>
      </div>

      <AnimatePresence>
        {results && (
          <motion.div 
            className="section"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ duration: 0.5 }}
          >
            <h3>Retrieval Metrics</h3>
            <div className="metrics-grid">
              <MetricCard label="Mean Reciprocal Rank (MRR)" value={results.mrr} metricType="mrr" />
              <MetricCard label="Normalized DCG (nDCG)" value={results.ndcg} metricType="ndcg" />
              <MetricCard label="Keyword Coverage" value={results.coverage} metricType="coverage" isPercentage={true} />
            </div>

            <h3 style={{ marginTop: '30px' }}>Answer Quality Metrics (LLM-as-a-judge)</h3>
            <div className="metrics-grid">
              <MetricCard label="Accuracy" value={results.accuracy} metricType="accuracy" scoreFormat={true} />
              <MetricCard label="Completeness" value={results.completeness} metricType="completeness" scoreFormat={true} />
              <MetricCard label="Relevance" value={results.relevance} metricType="relevance" scoreFormat={true} />
            </div>

            <div className="charts-container">
              <div className="chart-box">
                <div className="chart-title">Average MRR by Category</div>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={results.chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="category" stroke="#9ca3af" />
                    <YAxis domain={[0, 1]} stroke="#9ca3af" />
                    <Tooltip cursor={{fill: 'rgba(255,255,255,0.1)'}} contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151' }} />
                    <Legend />
                    <Bar dataKey="mrr" fill="#4f46e5" name="MRR Score" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="chart-box">
                <div className="chart-title">Average Accuracy by Category</div>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={results.chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="category" stroke="#9ca3af" />
                    <YAxis domain={[1, 5]} stroke="#9ca3af" />
                    <Tooltip cursor={{fill: 'rgba(255,255,255,0.1)'}} contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151' }} />
                    <Legend />
                    <Bar dataKey="accuracy" fill="#10b981" name="Accuracy (1-5)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default EvaluatorTab;
