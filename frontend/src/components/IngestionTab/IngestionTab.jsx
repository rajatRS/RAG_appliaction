import React, { useState } from 'react';
import Loader from '../Loader/Loader';
import { uploadFiles, uploadLocalFolder } from '../../api';
import './IngestionTab.css';

const IngestionTab = () => {
  const [files, setFiles] = useState(null);
  const [fileMetadata, setFileMetadata] = useState('');
  const [folderPath, setFolderPath] = useState('');
  const [folderMetadata, setFolderMetadata] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileUpload = async () => {
    if (!files || files.length === 0) {
      setStatus('Please select files first.');
      return;
    }
    setLoading(true);
    setStatus('Uploading and processing documents...');
    try {
      const res = await uploadFiles(files, fileMetadata);
      setStatus(`Success! ${res.message}\nChunks added: ${res.chunks_added}`);
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    }
    setLoading(false);
  };

  const handleFolderUpload = async () => {
    if (!folderPath) {
      setStatus('Please enter a folder path.');
      return;
    }
    setLoading(true);
    setStatus('Recursively scanning and vectorizing files...');
    try {
      const res = await uploadLocalFolder(folderPath, folderMetadata);
      setStatus(`Success! ${res.message}\nChunks added: ${res.chunks_added}`);
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    }
    setLoading(false);
  };

  return (
    <div className="tab-content">
      <div className="section">
        <h3>Option 1: Upload Files Manually</h3>
        <div className="input-group">
          <label>Select Documents (PDF, CSV, JSON, XLSX, DOCX)</label>
          <input type="file" multiple onChange={(e) => setFiles(e.target.files)} />
        </div>
        <div className="input-group">
          <label>Optional Metadata (JSON)</label>
          <input 
            type="text" 
            placeholder='{"category": "finance"}' 
            value={fileMetadata}
            onChange={(e) => setFileMetadata(e.target.value)}
          />
        </div>
        <button onClick={handleFileUpload} disabled={loading}>
          {loading ? <Loader text="Processing..." /> : 'Ingest Documents'}
        </button>
      </div>

      <div className="section">
        <h3>Option 2: Ingest Local Folder Recursively</h3>
        <div className="input-group">
          <label>Absolute Folder Path</label>
          <input 
            type="text" 
            placeholder="/Users/rajatshukla/Desktop/my_dataset" 
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
          />
        </div>
        <div className="input-group">
          <label>Optional Metadata (JSON)</label>
          <input 
            type="text" 
            placeholder='{"category": "finance"}' 
            value={folderMetadata}
            onChange={(e) => setFolderMetadata(e.target.value)}
          />
        </div>
        <button onClick={handleFolderUpload} disabled={loading}>
          {loading ? <Loader text="Scanning..." /> : 'Ingest Folder'}
        </button>
      </div>

      {status && (
        <div className={`status-box ${status.startsWith('Error') ? 'error' : ''}`}>
          {status}
        </div>
      )}
    </div>
  );
};

export default IngestionTab;
