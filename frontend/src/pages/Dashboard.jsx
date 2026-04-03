import { useState, useRef, useEffect } from 'react';
import { Bot, LineChart, Briefcase, ShieldCheck, Cloud, Upload, Zap, Send, FileText, ChevronRight, ChevronDown, Trash2, LogOut } from 'lucide-react';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import Plotly from 'plotly.js-dist-min';
import { supabase } from '../lib/supabase';

import './Dashboard.css';

// Native wrapper to completely bypass Vite's react-plotly.js compilation bug
const Plot = ({ data, layout, config, style, useResizeHandler }) => {
  const plotRef = useRef(null);

  useEffect(() => {
    if (plotRef.current) {
      Plotly.react(plotRef.current, data, layout, config);
    }
    
    // Optional: Handle resize if useResizeHandler is true
    const handleResize = () => {
      if (useResizeHandler && plotRef.current) {
        Plotly.Plots.resize(plotRef.current);
      }
    };
    
    if (useResizeHandler) {
      window.addEventListener('resize', handleResize);
    }
    return () => {
      if (useResizeHandler) {
        window.removeEventListener('resize', handleResize);
      }
      if (plotRef.current) {
        Plotly.purge(plotRef.current);
      }
    };
  }, [data, layout, config, useResizeHandler]);

  return <div ref={plotRef} style={style} />;
};

// Parse markdown formatting to JSX
const parseMarkdown = (text) => {
  if (!text) return '';
  
  // Split by markdown patterns and reconstruct with JSX
  const parts = [];
  let lastIndex = 0;
  
  // Match **bold**, *italic*, `code`, and plain text
  const regex = /\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`/g;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    // Add plain text before match
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex, match.index)
      });
    }
    
    // Add formatted match
    if (match[1]) {
      parts.push({
        type: 'bold',
        content: match[1]
      });
    } else if (match[2]) {
      parts.push({
        type: 'italic',
        content: match[2]
      });
    } else if (match[3]) {
      parts.push({
        type: 'code',
        content: match[3]
      });
    }
    
    lastIndex = regex.lastIndex;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.slice(lastIndex)
    });
  }
  
  // Convert parts to JSX
  return parts.map((part, idx) => {
    if (part.type === 'bold') {
      return <strong key={idx}>{part.content}</strong>;
    } else if (part.type === 'italic') {
      return <em key={idx}>{part.content}</em>;
    } else if (part.type === 'code') {
      return <code key={idx} style={{ 
        background: 'rgba(69, 243, 255, 0.1)', 
        padding: '0.2rem 0.5rem', 
        borderRadius: '4px',
        fontFamily: 'monospace'
      }}>{part.content}</code>;
    } else {
      return part.content;
    }
  });
};

const documentCategories = [
  { id: 'financial', title: 'Financial Reports', icon: <LineChart size={16} /> },
  { id: 'sales', title: 'Sales Reports', icon: <Briefcase size={16} /> },
  { id: 'investment', title: 'Investment Reports', icon: <ShieldCheck size={16} /> },
  { id: 'cloud', title: 'Cloud Documents', icon: <Cloud size={16} /> }
];

const agents = [
  { id: 'financial', name: 'Financial Analyst', icon: <LineChart size={18} /> },
  { id: 'sales', name: 'Sales Data Sci.', icon: <Briefcase size={18} /> },
  { id: 'investment', name: 'Investment Strat.', icon: <ShieldCheck size={18} /> },
  { id: 'cloud', name: 'Cloud Architect', icon: <Cloud size={18} /> }
];

// Determine a session ID for backend tracking
const SESSION_ID = "session_" + Math.random().toString(36).substring(2, 9);
const API_BASE = "http://127.0.0.1:8000/api";

const Dashboard = () => {
  const [inputMessage, setInputMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingState, setThinkingState] = useState(null); // 'orchestrator' | 'specialist'
  const [isUploading, setIsUploading] = useState(false); // <--- Prevent race conditions
  const [userInitials, setUserInitials] = useState('U');
  const [userName, setUserName] = useState('User');
  const [showLogoutMenu, setShowLogoutMenu] = useState(false);
  const navigate = useNavigate();

  // File state (maps category id to an array of uploaded files)
  const [uploadedFiles, setUploadedFiles] = useState({
    financial: [], sales: [], investment: [], cloud: []
  });
  const [expandedCategories, setExpandedCategories] = useState({
    financial: true, sales: false, investment: false, cloud: false
  });

  const chatEndRef = useRef(null);

  // Fetch user profile on mount
  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
          // Extract initials from email or name
          const email = user.email || 'User';
          const displayName = user.user_metadata?.name || email.split('@')[0];
          const initials = displayName.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase();
          setUserInitials(initials || 'U');
          setUserName(displayName);
        }
      } catch (err) {
        console.error('Failed to fetch user:', err);
      }
    };
    
    fetchUserProfile();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isThinking]);

  const toggleCategory = (id) => {
    setExpandedCategories(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleFileUpload = async (categoryId, e) => {
    if (e.target.files && e.target.files.length > 0) {
      const filesArr = Array.from(e.target.files);

      // Optimistically update UI
      const newFiles = filesArr.map(file => ({
        id: Date.now() + Math.random(),
        name: file.name,
        size: file.size
      }));
      setUploadedFiles(prev => ({
        ...prev,
        [categoryId]: [...prev[categoryId], ...newFiles]
      }));

      // Send to FastAPI Backend
      setIsUploading(true);
      const formData = new FormData();
      formData.append('session_id', SESSION_ID);
      formData.append('collection', categoryId);
      for (const file of filesArr) {
        formData.append('files', file);
      }

      try {
        await fetch(`${API_BASE}/upload`, {
          method: 'POST',
          body: formData,
        });
      } catch (err) {
        console.error("Failed to upload to backend API", err);
      } finally {
        setIsUploading(false);
      }
    }
  };

  const removeFile = (categoryId, fileId) => {
    setUploadedFiles(prev => ({
      ...prev,
      [categoryId]: prev[categoryId].filter(f => f.id !== fileId)
    }));
  };

  const clearAllData = async () => {
    setChatHistory([]);
    setUploadedFiles({ financial: [], sales: [], investment: [], cloud: [] });
    // Tell backend to clear session
    try {
      await fetch(`${API_BASE}/clear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID })
      });
    } catch { }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const queryText = inputMessage;
    const newMessage = {
      id: Date.now(),
      sender: 'user',
      text: queryText,
    };

    setChatHistory(prev => [...prev, newMessage]);
    setInputMessage('');

    // 1. Orchestrator starts thinking
    setIsThinking(true);
    setThinkingState('orchestrator');

    // Announce routing (Simulation for UX speed, actual work done underneath)
    const orchestratorMsg = {
      id: Date.now() + 1,
      sender: 'orchestrator',
      isGirl: true,
      text: `Got it. Let me analyze that and get you the best answer.`
    };
    setChatHistory(prev => [...prev, orchestratorMsg]);
    setThinkingState('specialist');

    // 2. Transmit query to FastAPI
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID, query: queryText })
      });

      const data = await res.json();
      setIsThinking(false);
      setThinkingState(null);

      if (data.success) {
        setChatHistory(prev => [
          ...prev,
          {
            id: Date.now() + 2,
            sender: data.agents?.[0] || 'orchestrator',
            isGirl: false,
            text: data.final_answer,
            agents_used: data.agents_summary,
            visualizations: data.visualizations
          }
        ]);
      } else {
        setChatHistory(prev => [
          ...prev,
          {
            id: Date.now() + 2,
            sender: 'orchestrator',
            isGirl: true,
            text: `Error processing request: ${data.error}`
          }
        ]);
      }
    } catch (err) {
      setIsThinking(false);
      setThinkingState(null);
      setChatHistory(prev => [
        ...prev,
        {
          id: Date.now() + 2,
          sender: 'orchestrator',
          isGirl: true,
          text: `I'm having trouble connecting. Please check that the analysis engine is running and try again.`
        }
      ]);
    }
  };

  const handleLogout = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      navigate('/');
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  return (
    <div className="dash-layout">
      {/* Top Navbar */}
      <nav className="dash-nav glass-panel">
        <Link to="/" className="dash-brand" style={{ textDecoration: 'none' }}>
          <Zap className="logo-icon-small" />
          <span>FinPilot-AI</span>
        </Link>

        <div className="dash-nav-actions" style={{ display: 'flex', alignItems: 'center', gap: '15px', position: 'relative' }}>
          <Link to="/" className="btn-secondary btn-sm" style={{ textDecoration: 'none' }}>
            Return to Home
          </Link>
          <div 
            className="user-avatar" 
            title={userName}
            onClick={() => setShowLogoutMenu(!showLogoutMenu)}
            style={{ cursor: 'pointer' }}
          >
            {userInitials}
          </div>
          {showLogoutMenu && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="logout-menu"
              style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '0.5rem',
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                padding: '0.5rem',
                zIndex: 1000,
                minWidth: '180px',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
              }}
            >
              <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-color)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                {userName}
              </div>
              <button 
                onClick={handleLogout}
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  border: 'none',
                  background: 'transparent',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  fontSize: '0.95rem',
                  transition: 'all 0.2s ease',
                  borderRadius: '8px'
                }}
                onMouseEnter={(e) => e.target.style.background = 'rgba(69, 243, 255, 0.1)'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}
              >
                <LogOut size={16} />
                Sign Out
              </button>
            </motion.div>
          )}
        </div>
      </nav>

      <div className="dash-body">
        {/* Document Upload Sidebar */}
        <aside className="upload-sidebar glass-panel">

          <div className="sidebar-header-action">
            <button className="btn-secondary btn-sm" style={{ width: '100%' }} onClick={clearAllData}>
              New Session / Clear Data
            </button>
          </div>

          <h3 className="sidebar-heading">Upload Documents</h3>

          <div className="document-categories">
            {documentCategories.map(cat => (
              <div key={cat.id} className="category-section">
                <div
                  className={`category-header ${expandedCategories[cat.id] ? 'expanded' : ''}`}
                  onClick={() => toggleCategory(cat.id)}
                >
                  <div className="cat-title-wrap">
                    {expandedCategories[cat.id] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    {cat.icon}
                    <span>{cat.title}</span>
                  </div>
                  <span className="file-count">{uploadedFiles[cat.id]?.length || 0}</span>
                </div>

                <AnimatePresence>
                  {expandedCategories[cat.id] && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="category-content"
                    >
                      <label className="upload-dropzone">
                        <Upload size={18} />
                        <span>Add {cat.title}</span>
                        <input
                          type="file"
                          multiple
                          accept=".pdf,.csv,.xlsx,.docx"
                          style={{ display: 'none' }}
                          onChange={(e) => handleFileUpload(cat.id, e)}
                        />
                      </label>

                      {uploadedFiles[cat.id].length > 0 && (
                        <div className="file-list">
                          {uploadedFiles[cat.id].map(file => (
                            <div key={file.id} className="file-item">
                              <FileText size={14} className="file-icon" />
                              <span className="file-name" title={file.name}>{file.name}</span>
                              <button className="remove-file-btn" onClick={() => removeFile(cat.id, file.id)}>
                                <Trash2 size={12} />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>

          <div className="sidebar-status">
            <div className="status-indicator">
              <span className="status-dot green"></span>
              System Ready
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="dash-main chat-mode">
          {chatHistory.length === 0 ? (
            // Empty State Layout
            <div className="empty-state animate-fade-in">
              <div className="orchestrator-girl-visual">
                <DotLottieReact
                  src="https://lottie.host/b0509e8f-790d-4dd3-811b-6a04c7fa7046/4h1nn1KhvX.lottie"
                  loop
                  autoplay
                  className="orchestrator-lottie"
                />
              </div>
              <h2 style={{ fontSize: '1.75rem', marginTop: '1rem', marginBottom: '0.5rem' }}>
                Welcome to your financial command center.
              </h2>
              <p style={{ maxWidth: '450px', margin: '0 auto 2rem' }}>
                Upload your documents, then ask me anything about your business. I'll analyze your data and get you clear, actionable answers from our specialist team.
              </p>

              <div className="suggested-prompts">
                <button onClick={() => setInputMessage("What are our sales trends? Show me a revenue breakdown.")} className="prompt-chip">
                  Show me sales trends and revenue breakdown
                </button>
                <button onClick={() => setInputMessage("Where can we cut costs and improve efficiency?")} className="prompt-chip">
                  Where can we optimize our costs?
                </button>
              </div>
            </div>
          ) : (
            // Chat History Layout
            <div className="chat-feed-container flex-1">
              <div className="chat-feed pb-20">
                {chatHistory.map((msg) => (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    key={msg.id}
                    className={`chat-row ${msg.sender === 'user' ? 'row-user' : 'row-agent'}`}
                  >
                    {msg.sender !== 'user' && (
                      <div className={`agent-avatar-icon ${msg.isGirl ? 'orchestrator-avatar' : 'specialist-avatar'}`}>
                        {msg.isGirl ? (
                          <DotLottieReact
                            src="https://lottie.host/b0509e8f-790d-4dd3-811b-6a04c7fa7046/4h1nn1KhvX.lottie"
                            loop
                            autoplay
                            style={{ width: '80%', height: '80%' }}
                          />
                        ) : (
                          agents.find(a => a.id === msg.sender)?.icon || <Bot size={20} />
                        )}
                      </div>
                    )}

                    <div className={`chat-bubble-new ${msg.sender === 'user' ? 'bubble-user' : 'bubble-agent'}`}>
                      {msg.sender !== 'user' && (
                        <div className="agent-name-tag">
                          {msg.isGirl ? 'Orchestrator' : agents.find(a => a.id === msg.sender)?.name || 'FinPilot Agent'}
                          {msg.agents_used && <span className="used-agents-badge">via {msg.agents_used}</span>}
                        </div>
                      )}

                      {/* Text content from agent */}
                      <div className="bubble-text" style={{ whiteSpace: "pre-wrap" }}>
                        {parseMarkdown(msg.text)}
                      </div>

                      {/* Display Data Visualizations if returned by API */}
                      {msg.visualizations && Object.entries(msg.visualizations).map(([agentName, plotData], idx) => (
                        <div key={idx} className="chart-render-box">
                          <h4 style={{ margin: '15px 0 5px', color: 'var(--accent-primary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>
                            {agentName} Chart
                          </h4>
                          <Plot
                            data={plotData.data}
                            layout={{
                              ...plotData.layout,
                              autosize: true,
                              paper_bgcolor: 'rgba(0,0,0,0)',
                              plot_bgcolor: 'rgba(0,0,0,0)',
                              font: { color: '#F0EAD6' }
                            }}
                            useResizeHandler={true}
                            style={{ width: '100%', minHeight: '350px' }}
                            config={{ responsive: true, displayModeBar: false }}
                          />
                        </div>
                      ))}
                    </div>
                  </motion.div>
                ))}

                {isThinking && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="chat-row row-agent">
                    <div className={`agent-avatar-icon thinking ${thinkingState === 'orchestrator' ? 'orchestrator-avatar' : 'specialist-avatar'}`}>
                      {thinkingState === 'orchestrator' ? (
                        <DotLottieReact
                          src="https://lottie.host/b0509e8f-790d-4dd3-811b-6a04c7fa7046/4h1nn1KhvX.lottie"
                          loop
                          autoplay
                          style={{ width: '80%', height: '80%' }}
                        />
                      ) : (
                        <Bot size={20} />
                      )}
                    </div>
                    {thinkingState === 'orchestrator' ? (
                      <div className="thinking-indicator">
                        <span className="dot-bounce d1" style={{ background: 'var(--accent-secondary)' }}></span>
                        <span className="dot-bounce d2" style={{ background: 'var(--accent-secondary)' }}></span>
                        <span className="dot-bounce d3" style={{ background: 'var(--accent-secondary)' }}></span>
                      </div>
                    ) : (
                      // Specialist animation representation
                      <div className="specialist-thinking-lottie">
                        <DotLottieReact
                          src="https://lottie.host/8c198d23-305a-4a73-8339-8be4e712077d/xKhYgkRmWu.lottie"
                          loop
                          autoplay
                          style={{ height: '40px' }}
                        />
                      </div>
                    )}
                  </motion.div>
                )}
                <div ref={chatEndRef} />
              </div>
            </div>
          )}

          {/* Unified Chat Input Fixed at Bottom */}
          <div className="unified-input-wrapper">
            <form onSubmit={handleSendMessage} className="main-input-form glass-panel flex-row">
              <input
                type="text"
                className="main-chat-input"
                placeholder={isUploading ? "Processing documents... please wait" : "Ask me anything about your business..."}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={isUploading || isThinking}
              />

              <button
                type="submit"
                className={`main-send-btn attach-end ${isUploading ? 'btn-disabled' : ''}`}
                disabled={!inputMessage.trim() || isUploading || isThinking}
              >
                <Send size={18} /> {isUploading ? 'UPLOADING...' : 'SEND'}
              </button>
            </form>
            <div className="footer-disclaimer">
              Smart insights from your data. Always verify results before making important decisions.
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
