import React, { useState, useEffect, useRef } from 'react';
import { fetchAgentConfig, updateAgentConfig, uploadAgentDataset, runAgentTriage } from '../../api';
import './AgentTab.css';

const AgentTab = () => {
  // Config state
  const [name, setName] = useState('IT Incident Triage Agent');
  const [instructions, setInstructions] = useState('');
  const [modelName, setModelName] = useState('gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.3);
  const [knowledgeSource, setKnowledgeSource] = useState('vector_db');
  
  // Custom dataset file upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [configSuccess, setConfigSuccess] = useState(false);

  // Playground state
  const [ticketText, setTicketText] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);

  // Agent Output State
  const [terminalLogs, setTerminalLogs] = useState([]);
  const [triageResult, setTriageResult] = useState(null);
  const [isDeploying, setIsDeploying] = useState(false);
  const [isDeployed, setIsDeployed] = useState(false);

  // Typewriting log trace helpers
  const [currentLogIndex, setCurrentLogIndex] = useState(-1);
  const [logTrace, setLogTrace] = useState([]);

  useEffect(() => {
    // Load initial config
    const loadConfig = async () => {
      try {
        const config = await fetchAgentConfig();
        setName(config.name);
        setInstructions(config.instructions);
        setModelName(config.model_name || 'gpt-4o-mini');
        setTemperature(config.temperature ?? 0.3);
        setKnowledgeSource(config.knowledge_source || 'vector_db');
      } catch (err) {
        console.error('Error fetching agent configuration:', err);
      }
    };
    loadConfig();
  }, []);

  // Sync elapsed timer
  useEffect(() => {
    if (isRunning) {
      timerRef.current = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning]);

  // Handle Typewriter logs sequence
  useEffect(() => {
    if (currentLogIndex >= 0 && currentLogIndex < logTrace.length) {
      const delay = currentLogIndex === 0 ? 500 : 1200;
      const timeout = setTimeout(() => {
        setTerminalLogs((prev) => [...prev, logTrace[currentLogIndex]]);
        setCurrentLogIndex((prev) => prev + 1);
      }, delay);
      return () => clearTimeout(timeout);
    } else if (currentLogIndex >= logTrace.length && logTrace.length > 0) {
      // Completed all log traces, show final result
      setIsRunning(false);
    }
  }, [currentLogIndex, logTrace]);

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setIsConfiguring(true);
    setConfigSuccess(false);
    try {
      // 1. Upload custom logs if needed
      if (knowledgeSource === 'custom_file' && selectedFile) {
        setUploadStatus('Uploading legacy incidents dataset...');
        const fileResult = await uploadAgentDataset(selectedFile);
        setUploadStatus(`Dataset uploaded: ${fileResult.message}`);
      }

      // 2. Save core agent properties
      await updateAgentConfig({
        name,
        instructions,
        model_name: modelName,
        temperature,
        knowledge_source: knowledgeSource
      });

      setConfigSuccess(true);
      setTimeout(() => setConfigSuccess(false), 3000);
    } catch (err) {
      console.error(err);
      setUploadStatus(`Error: ${err.message}`);
    } finally {
      setIsConfiguring(false);
    }
  };

  const handleRunTriage = async (e) => {
    e.preventDefault();
    if (!ticketText.trim()) return;

    setIsRunning(true);
    setElapsedTime(0);
    setTriageResult(null);
    setTerminalLogs([]);
    setLogTrace([]);
    setCurrentLogIndex(-1);
    setIsDeployed(false);

    // Initial startup log
    setTerminalLogs([`[System] Initializing ${name} context...`]);

    try {
      const result = await runAgentTriage(ticketText);
      
      // Inject standard setup steps into Chain-of-Thought logs trace
      const initialLogs = [
        `[Agent Setup] Loaded model ${modelName} (Temp: ${temperature})`,
        `[Retrieval] Querying target database using '${knowledgeSource === 'vector_db' ? 'RAG Search' : 'Legacy dataset file'}'`,
        `[Matches Found] Found ${result.matches?.length || 0} historical incident logs.`
      ];

      // Append matched tickets detailed logs
      if (result.matches && result.matches.length > 0) {
        result.matches.forEach((m, idx) => {
          initialLogs.push(`  └─ Match #${idx + 1}: "${m.title}" (Confidence: ${(m.confidence * 100).toFixed(0)}%)`);
        });
      }

      // Append CoT reasoning trace steps
      const rawReasoning = result.reasoning_steps || [];
      const cotLogs = rawReasoning.map(step => `[Reasoning] ${step}`);

      cotLogs.push(`[Triage Decision] Classifying priority as "${result.priority}" for category "${result.category}"`);
      cotLogs.push(`[Triage Decision] Synthesizing step-by-step resolution steps...`);

      // Set the logs trace list to animate
      setLogTrace([...initialLogs, ...cotLogs]);
      setTriageResult(result);
      
      // Trigger the typewriting loop
      setCurrentLogIndex(0);
    } catch (err) {
      console.error(err);
      setTerminalLogs((prev) => [...prev, `[Fatal Error] Agent run crashed: ${err.message}`]);
      setIsRunning(false);
    }
  };

  const handleDeploy = () => {
    setIsDeploying(true);
    setTimeout(() => {
      setIsDeploying(false);
      setIsDeployed(true);
    }, 1500);
  };

  return (
    <div className="agent-container">
      <div className="agent-header">
        <h1>🤖 RAG Agent Studio</h1>
        <p>Build and test autonomous agents that learn from legacy incident logs and resolve tickets.</p>
      </div>

      <div className="agent-grid">
        {/* Left Column - Builder Dashboard */}
        <div className="agent-card builder-section">
          <h2>1. Assemble AI Triage Agent</h2>
          
          <form onSubmit={handleSaveConfig} className="agent-form">
            <div className="form-group">
              <label>Agent Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Legacy Systems Triage Agent"
                required
              />
            </div>

            <div className="form-group">
              <label>Role & Persona Instructions</label>
              <textarea
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                rows={4}
                placeholder="Instruct your agent on its role, classification guidelines, and resolution style..."
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group half">
                <label>Model</label>
                <select value={modelName} onChange={(e) => setModelName(e.target.value)}>
                  <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
                  <option value="gpt-4o-mini">gpt-4o-mini</option>
                  <option value="gpt-4-turbo">gpt-4-turbo</option>
                  <option value="gpt-4o">gpt-4o</option>
                </select>
              </div>

              <div className="form-group half">
                <label>Temperature ({temperature})</label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Knowledge & Learning Source</label>
              <select value={knowledgeSource} onChange={(e) => setKnowledgeSource(e.target.value)}>
                <option value="vector_db">Active Vector Database (RAG Ingestion)</option>
                <option value="custom_file">Upload Historical Resolution Logs (JSON/CSV)</option>
              </select>
            </div>

            {knowledgeSource === 'custom_file' && (
              <div className="file-uploader-zone">
                <label className="uploader-label">
                  <span className="upload-icon">📁</span>
                  <span>{selectedFile ? selectedFile.name : 'Select or drag Resolution log (.json, .csv)'}</span>
                  <input
                    type="file"
                    accept=".json,.csv"
                    onChange={(e) => setSelectedFile(e.target.files[0])}
                    className="hidden-file-input"
                  />
                </label>
                {selectedFile && (
                  <p className="file-ready-text">Ready: {(selectedFile.size / 1024).toFixed(1)} KB</p>
                )}
              </div>
            )}

            <button type="submit" className="btn-assemble" disabled={isConfiguring}>
              {isConfiguring ? 'Compiling Agent Model...' : '🚀 Assemble Agent Profile'}
            </button>

            {configSuccess && (
              <div className="success-banner">✓ Agent assembled and saved successfully!</div>
            )}
            {uploadStatus && <div className="status-text">{uploadStatus}</div>}
          </form>
        </div>

        {/* Right Column - Playground & Console */}
        <div className="agent-card playground-section">
          <h2>2. Triage & Triage Incident</h2>
          
          <form onSubmit={handleRunTriage} className="playground-form">
            <div className="form-group">
              <label>Paste Raw Verbose Incident Ticket</label>
              <textarea
                value={ticketText}
                onChange={(e) => setTicketText(e.target.value)}
                rows={5}
                placeholder="Paste the user description of the issue. E.g.: 'Macbook client reports database connection failed. Cannot connect to staging cluster, timeout 504. Tried DNS flush but network is blocked.'"
                required
              />
            </div>
            
            <button type="submit" className="btn-triage" disabled={isRunning || !ticketText.trim()}>
              {isRunning ? `Triage Running... (${elapsedTime}s)` : '🤖 Execute Agent Triage'}
            </button>
          </form>

          {/* Console / Terminal logs */}
          {(terminalLogs.length > 0) && (
            <div className="console-wrapper">
              <div className="console-header">
                <span className="dot red"></span>
                <span className="dot yellow"></span>
                <span className="dot green"></span>
                <span className="console-title">{name} Terminal Logs</span>
              </div>
              <div className="console-body">
                {terminalLogs.map((log, idx) => (
                  <div key={idx} className={`console-line ${log.startsWith('[Fatal') ? 'error' : log.startsWith('[System') ? 'system' : log.startsWith('[Retrieval') || log.startsWith('  └') ? 'retrieve' : ''}`}>
                    {log}
                  </div>
                ))}
                {isRunning && <div className="console-cursor">_</div>}
              </div>
            </div>
          )}

          {/* Final Suggestions Output Card */}
          {(!isRunning && triageResult) && (
            <div className="result-card fade-in">
              <div className="result-header">
                <h3>Agent Solution Card</h3>
                <span className={`priority-badge ${triageResult.priority?.toLowerCase()}`}>
                  {triageResult.priority}
                </span>
              </div>

              <div className="result-grid">
                <div className="result-meta">
                  <div className="meta-item">
                    <span className="meta-label">Category:</span>
                    <span className="meta-val">{triageResult.category}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Matches:</span>
                    <span className="meta-val">{triageResult.matches?.length || 0} Incident References</span>
                  </div>
                </div>

                <div className="confidence-circle-box">
                  <svg className="confidence-svg" viewBox="0 0 36 36">
                    <path
                      className="circle-bg"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className="circle-progress"
                      strokeDasharray={`${(triageResult.confidence * 100).toFixed(0)}, 100`}
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <text x="18" y="20.35" className="circle-number">{(triageResult.confidence * 100).toFixed(0)}%</text>
                  </svg>
                  <span className="confidence-label">Agent Confidence</span>
                </div>
              </div>

              <div className="suggested-resolution">
                <h4>Suggested Resolution Guide</h4>
                <div className="resolution-content">
                  {triageResult.suggested_resolution.split('\n').map((line, idx) => {
                    if (line.startsWith('###')) {
                      return <h5 key={idx}>{line.replace('###', '')}</h5>;
                    }
                    if (line.startsWith('-') || line.startsWith('*')) {
                      return <li key={idx}>{line.substring(1).trim()}</li>;
                    }
                    return <p key={idx}>{line}</p>;
                  })}
                </div>
              </div>

              <button 
                onClick={handleDeploy} 
                className={`btn-deploy ${isDeployed ? 'deployed' : ''}`}
                disabled={isDeploying || isDeployed}
              >
                {isDeploying ? 'Syncing to Jira...' : isDeployed ? '✓ Deployed & Ticket Closed' : '📤 Deploy Resolution to Ticketing System'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentTab;
