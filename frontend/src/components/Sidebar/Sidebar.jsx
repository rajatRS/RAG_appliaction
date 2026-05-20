import React from 'react';
import './Sidebar.css';

const Sidebar = ({ activeTab, setActiveTab }) => {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>🚀 RAG Dashboard</h1>
        <p>Enterprise AI Engine</p>
      </div>
      
      <nav className="sidebar-nav">
        <button 
          className={`nav-item ${activeTab === 'ingestion' ? 'active' : ''}`}
          onClick={() => setActiveTab('ingestion')}
        >
          <span className="nav-icon">📁</span>
          Document Ingestion
        </button>
        
        <button 
          className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <span className="nav-icon">💬</span>
          Chat & Query
        </button>

        <button 
          className={`nav-item ${activeTab === 'evaluator' ? 'active' : ''}`}
          onClick={() => setActiveTab('evaluator')}
        >
          <span className="nav-icon">📊</span>
          RAG Evaluator
        </button>

        <button 
          className={`nav-item ${activeTab === 'agent' ? 'active' : ''}`}
          onClick={() => setActiveTab('agent')}
        >
          <span className="nav-icon">🤖</span>
          Agent Studio
        </button>

        <button 
          className={`nav-item ${activeTab === 'orchestrator' ? 'active' : ''}`}
          onClick={() => setActiveTab('orchestrator')}
        >
          <span className="nav-icon">🌌</span>
          Multimodal Studio
        </button>
      </nav>
      
      <div className="sidebar-footer">
        <p>Built with FastAPI & React</p>
      </div>
    </div>
  );
};

export default Sidebar;
