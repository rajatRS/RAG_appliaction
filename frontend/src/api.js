const API_BASE = "http://localhost:8000/api";

export const uploadFiles = async (files, metadata) => {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }
  if (metadata) {
    formData.append("metadata", metadata);
  }

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  
  if (!response.ok) {
    const err = await response.text();
    throw new Error(err);
  }
  return response.json();
};

export const uploadLocalFolder = async (folderPath, metadata) => {
  const response = await fetch(`${API_BASE}/upload-local-folder`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ folder_path: folderPath, metadata }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(err);
  }
  return response.json();
};

export const querySystem = async (query, modelName, topK, searchType) => {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ 
      query, 
      top_k: topK, 
      model_name: modelName,
      search_type: searchType 
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(err);
  }
  return response.json();
};

export const evaluateSystem = async (file, topK, vectorStore, modelName) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('top_k', topK);
  formData.append('vector_store', vectorStore);
  formData.append('model_name', modelName);

  const response = await fetch(`${API_BASE}/evaluate`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to evaluate the system.');
  }

  return response.json();
};
