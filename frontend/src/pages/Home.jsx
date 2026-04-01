import { Link } from 'react-router-dom';
import { Bot, LineChart, ShieldCheck, Cloud, Briefcase, ChevronRight, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
import './Home.css';

const features = [
  {
    icon: <Bot size={28} />,
    title: 'Smart Assistant',
    desc: 'Understands your questions and connects you with the right expert for instant answers.'
  },
  {
    icon: <LineChart size={28} />,
    title: 'Financial Expert',
    desc: 'Analyzes profits, predicts cash flow, and reveals hidden spending patterns in your business.'
  },
  {
    icon: <Briefcase size={28} />,
    title: 'Sales Specialist',
    desc: 'Spots trends, predicts what will sell next, and alerts you to unusual patterns.'
  },
  {
    icon: <ShieldCheck size={28} />,
    title: 'Investment Advisor',
    desc: 'Evaluates opportunities, identifies smart moves, and helps you manage financial risks.'
  },
  {
    icon: <Cloud size={28} />,
    title: 'Infrastructure Expert',
    desc: 'Recommends ways to optimize your systems, reduce costs, and improve performance.'
  }
];

const Home = () => {
  return (
    <div className="home-container">
      {/* Background Orbs for Deep Theme */}
      <div className="bg-orb orb-1"></div>
      <div className="bg-orb orb-2"></div>
      
      {/* Navigation Layer */}
      <nav className="home-nav glass-panel">
        <div className="nav-logo">
          <Zap className="logo-icon" />
          <span>FinPilot-AI</span>
        </div>
        <div className="nav-links">
          <Link to="/login" className="btn-secondary">Sign In</Link>
          <Link to="/register" className="btn-primary">Start Analyzing</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content-wrapper">
          <motion.div 
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="hero-text"
          >
            <div className="badge">AI-Powered Financial Insights</div>
            <h1 className="hero-title">
              Smart Financial Analysis,<br/>
              <span className="highlight">Made Simple.</span>
            </h1>
            <p className="hero-description">
              Stop juggling spreadsheets and reports. Get instant, actionable insights from all your financial data in one place. 
              5 specialized AI experts work together to understand your business better.
            </p>
            
            <div className="hero-actions">
              <Link to="/register" className="btn-primary btn-lg shine-effect">
                Get Started <ChevronRight size={20} />
              </Link>
              <Link to="#features" className="btn-secondary btn-lg">
                Learn More
              </Link>
            </div>
            
            <div className="hero-stats">
              <div className="stat-item">
                <span className="stat-val">70%</span>
                <span className="stat-label">Faster Analysis</span>
              </div>
              <div className="stat-item">
                <span className="stat-val">5</span>
                <span className="stat-label">Specialized AI Agents</span>
              </div>
            </div>
          </motion.div>

          {/* Hero Visual: Lottie Animation */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hero-visual-3d"
          >
            <div className="lottie-wrapper-main glass-panel">
              <DotLottieReact
                src="https://lottie.host/650d0506-43a3-4f3b-87eb-df371356feab/0rq0fmn0fP.lottie"
                loop
                autoplay
                className="lottie-player"
              />
            </div>
          </motion.div>
        </div>
      </section>

      {/* Capabilities Section */}
      <section id="features" className="features-section">
        <div className="features-header">
          <h2>Meet Your Expert Team</h2>
          <p>5 specialized AI experts analyzing your data together, working as one to give you better answers.</p>
        </div>
        
        <div className="features-grid">
          {features.map((feat, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: idx * 0.1 }}
              viewport={{ once: true, margin: "-50px" }}
              className="feature-card glass-panel group"
            >
              <div className="feature-icon-wrapper">
                {feat.icon}
              </div>
              <h3>{feat.title}</h3>
              <p>{feat.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Deep Dive Lottie Section */}
      <section className="insight-section">
        <div className="insight-container">
          <motion.div 
             initial={{ opacity: 0, x: -30 }}
             whileInView={{ opacity: 1, x: 0 }}
             viewport={{ once: true }}
             className="insight-visual"
          >
             <DotLottieReact
                src="https://lottie.host/8c198d23-305a-4a73-8339-8be4e712077d/xKhYgkRmWu.lottie"
                loop
                autoplay
                className="lottie-player-sm"
              />
          </motion.div>
          <motion.div 
             initial={{ opacity: 0, x: 30 }}
             whileInView={{ opacity: 1, x: 0 }}
             viewport={{ once: true }}
             className="insight-text"
          >
            <h2>All your answers in seconds.</h2>
            <p>
              Upload your financial reports, sales data, and business documents. Ask any question, and the right expert will give you answers backed by your actual data—no more digging through spreadsheets.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Minimal Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-brand">
            <Zap className="logo-icon-small" />
            <span>FinPilot-AI</span>
          </div>
          <div className="footer-text">
            © 2026 FinPilot-AI. Advanced multi-agent financial intelligence.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
