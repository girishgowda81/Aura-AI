import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Github, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState(() => localStorage.getItem('aura_session_id') || null);
    const [sessions, setSessions] = useState([]);
    const messagesEndRef = useRef(null);

    const fetchSessions = async () => {
        try {
            const res = await axios.get(`${API_URL}/sessions`);
            setSessions(res.data);
        } catch (error) {
            console.error('Error fetching sessions:', error);
        }
    };

    const loadSession = async (id) => {
        setLoading(true);
        try {
            setSessionId(id);
            localStorage.setItem('aura_session_id', id);
            const res = await axios.get(`${API_URL}/history/${id}`);
            setMessages(res.data.map(m => ({ role: m.role, content: m.content })));
        } catch (error) {
            console.error('Error loading session:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setSessionId(null);
        localStorage.removeItem('aura_session_id');
    };

    // Load history and sessions on mount
    useEffect(() => {
        fetchSessions();
        const savedSession = localStorage.getItem('aura_session_id');
        if (savedSession) {
            loadSession(savedSession);
        }
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const response = await axios.post(`${API_URL}/chat`, {
                messages: [...messages, userMsg],
                session_id: sessionId
            });

            const assistantMsg = { role: 'assistant', content: response.data.content };
            setMessages(prev => [...prev, assistantMsg]);
            if (!sessionId) {
                setSessionId(response.data.session_id);
                localStorage.setItem('aura_session_id', response.data.session_id);
                fetchSessions();
            }
        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error. Is the backend running?' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app-container">
            <div className="bg-mesh" />

            <nav className="navbar">
                <div className="nav-brand">
                    <div className="brand-icon">
                        <Bot size={24} color="white" />
                    </div>
                    <span className="brand-name">Giri AI</span>
                </div>
                <div className="nav-actions">
                    <a href="https://github.com" target="_blank" rel="noreferrer" style={{ color: 'inherit' }}>
                        <Github size={20} className="icon-muted" />
                    </a>
                </div>
            </nav>

            <main className="main-layout">
                <aside className="sidebar">
                    <button className="new-chat-btn" onClick={handleNewChat}>
                        <MessageSquare size={16} /> New Chat
                    </button>
                    <div style={{ flex: 1, overflowY: 'auto', marginTop: '20px' }}>
                        <p style={{ fontSize: '10px', fontWeight: 'bold', color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', marginBottom: '10px' }}>Recent Chats</p>
                        <div className="sessions-list">
                            {sessions.map((s) => (
                                <button
                                    key={s.session_id}
                                    className={`session-item ${sessionId === s.session_id ? 'active' : ''}`}
                                    onClick={() => loadSession(s.session_id)}
                                >
                                    <MessageSquare size={14} />
                                    <span>Chat {s.session_id.substring(0, 8)}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </aside>

                <section className="chat-container">
                    <div className="messages-area custom-scrollbar">
                        <AnimatePresence>
                            {messages.length === 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="welcome-screen"
                                >
                                    <Bot size={64} style={{ marginBottom: '16px', color: 'var(--primary)' }} />
                                    <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '8px' }}>Welcome to Aura AI</h2>
                                    <p style={{ maxWidth: '400px', fontSize: '14px' }}>Experience the next generation of conversational intelligence. How can I assist you today?</p>
                                </motion.div>
                            )}
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`message-wrapper ${msg.role}`}>
                                    <div className="message-bubble">
                                        <div style={{ marginTop: '4px' }}>
                                            {msg.role === 'user' ? <User size={18} /> : <Bot size={18} style={{ color: 'var(--primary)' }} />}
                                        </div>
                                        <div style={{ fontSize: '14px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                                            {msg.content}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div className="message-wrapper assistant">
                                    <div className="message-bubble">
                                        <Bot size={18} style={{ color: 'var(--primary)' }} />
                                        <div className="loading-dots">
                                            <div className="dot" style={{ animationDelay: '0s' }} />
                                            <div className="dot" style={{ animationDelay: '0.2s' }} />
                                            <div className="dot" style={{ animationDelay: '0.4s' }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="input-area">
                        <form className="input-form" onSubmit={handleSend}>
                            <input
                                className="chat-input"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Message Aura AI..."
                            />
                            <button
                                type="submit"
                                className="send-btn"
                                disabled={loading || !input.trim()}
                            >
                                <Send size={20} />
                            </button>
                        </form>
                        <p style={{ textAlign: 'center', fontSize: '10px', marginTop: '10px', color: 'rgba(255,255,255,0.2)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                            Aura AI can make mistakes. Check important info.
                        </p>
                    </div>
                </section>
            </main>
        </div>
    );
}

export default App;
