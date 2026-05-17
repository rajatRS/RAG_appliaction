import React, { useState, useEffect } from 'react';
import './Loader.css';

const Loader = ({ text, showTimer = false }) => {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    let interval;
    if (showTimer) {
      interval = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [showTimer]);

  return (
    <div className="loader-container">
      <span className="spinner"></span>
      {text && <span className="loader-text">{text} {showTimer && `(${seconds}s)`}</span>}
    </div>
  );
};

export default Loader;
