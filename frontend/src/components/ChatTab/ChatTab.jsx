import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Loader from '../Loader/Loader';
import { querySystem } from '../../api';
import './ChatTab.css';

const ChatTab = () => {
  const [query, setQuery] = useState('');
  const [model, setModel] = useState('gpt-3.5-turbo');
  const [topK, setTopK] = useState(5);
  const [searchType, setSearchType] = useState('dense');
  const [usePinecone, setUsePinecone] = useState(false);
  
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    if (!query) return;
    
    const topKNum = parseInt(topK);
    if (isNaN(topKNum) || topKNum < 0 || topKNum > 20) {
        alert("The values are out of bound, please keep it between 0-20.");
        return;
    }

    setLoading(true);
    setAnswer('Thinking...');
    setSources([]);
    try {
      const vectorStore = usePinecone ? "pinecone" : "chroma";
      // If not using Pinecone, we force dense search
      const finalSearchType = usePinecone ? searchType : "dense";
      
      const res = await querySystem(query, model, topKNum, finalSearchType, vectorStore);
      setAnswer(res.answer);
      setSources(res.sources);
    } catch (err) {
      setAnswer(`Error: ${err.message}`);
    }
    setLoading(false);
  };

  return (
    <motion.div 
      className="chat-tab"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <div className="section controls-section">
        <div className="chat-container">
          <div className="input-group flex-1">
            <label>Ask a Question (Expands to 3 queries)</label>
            <input 
              type="text" 
              placeholder="What does the document say about X?" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
            />
          </div>
          <div className="input-group flex-none">
            <label>LLM Model</label>
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
            <label>Top K Results (0-20)</label>
            <input 
              type="number" 
              min="0" 
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
                  onChange={(e) => {
                    setUsePinecone(e.target.checked);
                    if (!e.target.checked) setSearchType('dense');
                  }} 
                />
                <span className="slider round"></span>
              </label>
              <label style={{ marginBottom: 0 }}>Pinecone Vector Store</label>
            </div>
            
            {usePinecone && (
              <div className="toggle-buttons">
                <button 
                  className={`toggle-btn ${searchType === 'dense' ? 'active' : ''}`}
                  onClick={() => setSearchType('dense')}
                >
                  Dense Only
                </button>
                <button 
                  className={`toggle-btn ${searchType === 'sparse' ? 'active' : ''}`}
                  onClick={() => setSearchType('sparse')}
                >
                  Sparse Only
                </button>
                <button 
                  className={`toggle-btn ${searchType === 'hybrid' ? 'active' : ''}`}
                  onClick={() => setSearchType('hybrid')}
                >
                  Hybrid
                </button>
              </div>
            )}
          </div>
        </div>

        <button className="submit-btn" onClick={handleQuery} disabled={loading || !query}>
          {loading ? <Loader text="Querying, Reranking, Generating..." showTimer={true} /> : 'Submit Query'}
        </button>
      </div>

      <div className="section results-section">
        <h3>Answer</h3>
        <textarea 
          readOnly 
          value={answer} 
          placeholder="The answer will appear here..."
        />
        
        <AnimatePresence>
          {sources.length > 0 && (
            <motion.div 
              className="sources-container"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              transition={{ duration: 0.5 }}
            >
              <h3>Sources Used & Rerank Confidence</h3>
              <div className="sources-box">
                {sources.map((s, idx) => (
                  <motion.div 
                    key={idx} 
                    className="source-item"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                  >
                    <div className="source-meta">
                      <strong>Source:</strong> {s.source} 
                      <span className="score-badge">{s.confidence_score}</span>
                    </div>
                    <span className="source-content">{s.page_content}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default ChatTab;
