import React, { useState, useEffect, useRef } from 'react';
import { runOrchestration, archiveOrchestrationCase } from '../../api';
import './OrchestratorTab.css';

const OrchestratorTab = () => {
  // Input fields state
  const [ticketText, setTicketText] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  
  // Sub-agents checklist
  const [subAgents, setSubAgents] = useState({
    network: true,
    database: true,
    security: true
  });

  // Runner execution states
  const [isRunning, setIsRunning] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);

  // Animate terminal typewriter states
  const [terminalLogs, setTerminalLogs] = useState([]);
  const [logTrace, setLogTrace] = useState([]);
  const [currentLogIndex, setCurrentLogIndex] = useState(-1);

  // Diagnostic Outputs
  const [diagnosticsResult, setDiagnosticsResult] = useState(null);
  const [subReports, setSubReports] = useState({});
  const [activeSpecialist, setActiveSpecialist] = useState(null);

  // Archival States
  const [isArchiving, setIsArchiving] = useState(false);
  const [archiveMsg, setArchiveMsg] = useState('');

  // Clean up image previews on unmount
  useEffect(() => {
    return () => {
      if (imagePreview) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview]);

  // Handle Elapsed Timer
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

  // Typewriting logic for orchestration logs console
  useEffect(() => {
    if (currentLogIndex >= 0 && currentLogIndex < logTrace.length) {
      const logLine = logTrace[currentLogIndex];
      
      // Determine active specialist highlight based on log statements
      if (logLine.includes("Network Specialist")) {
        setActiveSpecialist("network");
      } else if (logLine.includes("Database Specialist")) {
        setActiveSpecialist("database");
      } else if (logLine.includes("Security Specialist")) {
        setActiveSpecialist("security");
      } else if (logLine.includes("Phase 3")) {
        setActiveSpecialist(null);
      }

      const delay = currentLogIndex === 0 ? 300 : 1500;
      const timeout = setTimeout(() => {
        setTerminalLogs((prev) => [...prev, logLine]);
        setCurrentLogIndex((prev) => prev + 1);
      }, delay);
      return () => clearTimeout(timeout);
    } else if (currentLogIndex >= logTrace.length && logTrace.length > 0) {
      setIsRunning(false);
      setActiveSpecialist(null);
    }
  }, [currentLogIndex, logTrace]);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      if (imagePreview) URL.revokeObjectURL(imagePreview);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleClearImage = (e) => {
    e.preventDefault();
    setSelectedImage(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
  };

  const handleToggleAgent = (agentKey) => {
    setSubAgents((prev) => ({
      ...prev,
      [agentKey]: !prev[agentKey]
    }));
  };

  const handleSubmitDiagnostics = async (e) => {
    e.preventDefault();
    if (!ticketText.trim()) return;

    setIsRunning(true);
    setElapsedTime(0);
    setDiagnosticsResult(null);
    setTerminalLogs([]);
    setLogTrace([]);
    setCurrentLogIndex(-1);
    setSubReports({});
    setActiveSpecialist(null);
    setArchiveMsg('');

    // Determine enabled sub-agent string identifiers
    const enabledSubagents = Object.keys(subAgents).filter(k => subAgents[k]);

    setTerminalLogs(["[Orchestrator] Spinlock validation complete. Booting Orchestrator..."]);

    try {
      const response = await runOrchestration(ticketText, selectedImage, enabledSubagents);
      
      setDiagnosticsResult(response);
      setSubReports(response.sub_reports || {});
      
      // Inject returned trace logs into typewriter queue
      const rawLogs = response.logs || [
        "[Orchestrator] Orchestration completed successfully.",
        "[Orchestrator] Unified resolutions synthesized."
      ];
      setLogTrace(rawLogs);
      setCurrentLogIndex(0);
    } catch (err) {
      console.error(err);
      setTerminalLogs((prev) => [...prev, `[Fatal Error] Pipeline crashed: ${err.message}`]);
      setIsRunning(false);
    }
  };

  const handleArchiveCase = async () => {
    if (!diagnosticsResult) return;
    setIsArchiving(true);
    setArchiveMsg('');
    try {
      const payload = {
        customer_name: diagnosticsResult.customer_name || "Autonomous Triage Diagnostics",
        department: diagnosticsResult.department || "Operations",
        issue_category: diagnosticsResult.issue_category || "General",
        priority: diagnosticsResult.priority || "Medium",
        issue_description: diagnosticsResult.issue_description || ticketText,
        resolution_steps: diagnosticsResult.resolution_steps || [],
        resolution_summary: diagnosticsResult.resolution_summary || ""
      };
      
      const response = await archiveOrchestrationCase(payload);
      setArchiveMsg(`✓ Successfully archived to learning logs as Case ${response.ticket_id}!`);
    } catch (err) {
      console.error(err);
      setArchiveMsg(`Error archiving case: ${err.message}`);
    } finally {
      setIsArchiving(false);
    }
  };

  return (
    <div className="orchestrator-container">
      <div className="orchestrator-header">
        <h1>🌌 Multimodal Orchestrator Studio</h1>
        <p>Analyze screen capture files and trigger collaborative specialized diagnostics to solve incidents.</p>
      </div>

      <div className="orchestrator-grid">
        {/* Left Panel: Configuration Form */}
        <div className="orchestrator-card inputs-section">
          <h2>1. Diagnosis Inputs</h2>
          
          <form onSubmit={handleSubmitDiagnostics} className="orchestrator-form">
            <div className="form-group">
              <label>Incident Details / Stack Trace logs</label>
              <textarea
                value={ticketText}
                onChange={(e) => setTicketText(e.target.value)}
                rows={5}
                placeholder="Describe the incident, error code, or system warning logs..."
                required
              />
            </div>

            <div className="form-group">
              <label>Attach Screenshot / Error Visual Capture</label>
              <div className="uploader-box">
                {imagePreview ? (
                  <div className="image-preview-wrapper">
                    <img src={imagePreview} alt="Incident Screen preview" className="thumbnail-preview" />
                    <button className="btn-clear-image" onClick={handleClearImage}>Clear Capture ✕</button>
                  </div>
                ) : (
                  <label className="uploader-area">
                    <span className="uploader-icon">📸</span>
                    <span className="uploader-text">Upload Screen Log (.png, .jpg, .jpeg)</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageChange}
                      className="hidden-file-input"
                    />
                  </label>
                )}
              </div>
            </div>

            <div className="form-group">
              <label>Assign Specialized Diagnostic Sub-Agents</label>
              <div className="specialists-list">
                <div 
                  className={`specialist-checkbox-wrapper ${subAgents.network ? 'active' : ''}`}
                  onClick={() => handleToggleAgent('network')}
                >
                  <span className="specialist-check">🌐</span>
                  <div className="specialist-info">
                    <h4>Network Specialist</h4>
                    <p>Diagnoses firewalls, port accesses, DNS resolution issues.</p>
                  </div>
                </div>

                <div 
                  className={`specialist-checkbox-wrapper ${subAgents.database ? 'active' : ''}`}
                  onClick={() => handleToggleAgent('database')}
                >
                  <span className="specialist-check">💾</span>
                  <div className="specialist-info">
                    <h4>Database Specialist</h4>
                    <p>Diagnoses locks, slow queries, pools connection leaks.</p>
                  </div>
                </div>

                <div 
                  className={`specialist-checkbox-wrapper ${subAgents.security ? 'active' : ''}`}
                  onClick={() => handleToggleAgent('security')}
                >
                  <span className="specialist-check">🔒</span>
                  <div className="specialist-info">
                    <h4>Security Specialist</h4>
                    <p>Reviews expired SSL keys, tokens auth policy blocks.</p>
                  </div>
                </div>
              </div>
            </div>

            <button type="submit" className="btn-run-diagnostics" disabled={isRunning || !ticketText.trim()}>
              {isRunning ? `Diagnostics Active... (${elapsedTime}s)` : '⚙ Run Orchestrated Diagnostics'}
            </button>
          </form>
        </div>

        {/* Right Panel: Collaborative Diagnostics & Outputs */}
        <div className="orchestrator-card diagnostics-section">
          <h2>2. Live Operations Console</h2>

          {/* Sub-agent Collaboration Diagram */}
          {isRunning && (
            <div className="collaboration-map">
              <div className={`map-node orchestrator active`}>
                🧠 Orchestrator
              </div>
              <div className="map-connectors">
                <div className={`connector-line ${activeSpecialist === 'network' ? 'pulsing' : ''}`}></div>
                <div className={`connector-line ${activeSpecialist === 'database' ? 'pulsing' : ''}`}></div>
                <div className={`connector-line ${activeSpecialist === 'security' ? 'pulsing' : ''}`}></div>
              </div>
              <div className="specialist-nodes">
                <div className={`map-node specialist ${activeSpecialist === 'network' ? 'active' : ''}`}>
                  🌐 Network Specialist
                </div>
                <div className={`map-node specialist ${activeSpecialist === 'database' ? 'active' : ''}`}>
                  💾 Database Specialist
                </div>
                <div className={`map-node specialist ${activeSpecialist === 'security' ? 'active' : ''}`}>
                  🔒 Security Specialist
                </div>
              </div>
            </div>
          )}

          {/* Typewriter logs terminal */}
          {(terminalLogs.length > 0) && (
            <div className="console-wrapper">
              <div className="console-header">
                <span className="dot red"></span>
                <span className="dot yellow"></span>
                <span className="dot green"></span>
                <span className="console-title">Orchestration Diagnostics Trace</span>
              </div>
              <div className="console-body">
                {terminalLogs.map((log, idx) => (
                  <div key={idx} className={`console-line ${log.startsWith('[Fatal') ? 'error' : log.includes('Orchestrator') ? 'system' : 'retrieve'}`}>
                    {log}
                  </div>
                ))}
                {isRunning && <span className="console-cursor">_</span>}
              </div>
            </div>
          )}

          {/* Unified Resolution Card */}
          {(!isRunning && diagnosticsResult) && (
            <div className="resolution-card fade-in">
              <div className="resolution-card-header">
                <h3>Unified Resolution Case Summary</h3>
                <span className={`priority-badge ${diagnosticsResult.priority?.toLowerCase()}`}>
                  {diagnosticsResult.priority}
                </span>
              </div>

              <div className="resolution-meta-grid">
                <div className="meta-item">
                  <span className="meta-label">Category:</span>
                  <span className="meta-val">{diagnosticsResult.issue_category}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Department:</span>
                  <span className="meta-val">{diagnosticsResult.department}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Assigned Target:</span>
                  <span className="meta-val">{diagnosticsResult.customer_name}</span>
                </div>
              </div>

              <div className="resolution-text-box">
                <h4>Visual Vision Observations Summary</h4>
                <p className="description-content">{diagnosticsResult.issue_description}</p>
              </div>

              <div className="resolution-guide-box">
                <h4>Unified Resolution Action Steps</h4>
                <div className="steps-list">
                  {diagnosticsResult.resolution_steps?.map((step, idx) => (
                    <div key={idx} className="step-item">
                      <span className="step-number">{idx + 1}</span>
                      <span className="step-text">{step}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="resolution-summary-box">
                <h4>Resolution Diagnostics Conclusion</h4>
                <p className="summary-text">{diagnosticsResult.resolution_summary}</p>
              </div>

              {/* Specialists Diagnostic Briefs */}
              <div className="specialists-briefs">
                <h4>Specialist Diagnostic Reports</h4>
                <div className="briefs-grid">
                  {Object.keys(subReports).map((key) => {
                    if (key === 'orchestrator_initial') return null;
                    return (
                      <div key={key} className="brief-card">
                        <h5>{key.toUpperCase()} Specialist Report</h5>
                        <p>{subReports[key]}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              <button 
                onClick={handleArchiveCase} 
                className="btn-archive-resolution"
                disabled={isArchiving}
              >
                {isArchiving ? 'Archiving resolved Case log...' : '💾 Archive as Safe Resolution Log'}
              </button>

              {archiveMsg && (
                <div className={`archive-banner ${archiveMsg.startsWith('Error') ? 'error' : ''}`}>
                  {archiveMsg}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OrchestratorTab;
