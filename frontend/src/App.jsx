import React, { useState } from 'react';
import Sidebar from './components/Sidebar/Sidebar';
import IngestionTab from './components/IngestionTab/IngestionTab';
import ChatTab from './components/ChatTab/ChatTab';
import EvaluatorTab from './components/EvaluatorTab/EvaluatorTab';
import './index.css'; // Global styles

function App() {
  const [activeTab, setActiveTab] = useState('ingestion');

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {activeTab === 'ingestion' && <IngestionTab />}
        {activeTab === 'chat' && <ChatTab />}
        {activeTab === 'evaluator' && <EvaluatorTab />}
      </main>
    </div>
  );
}

export default App;
