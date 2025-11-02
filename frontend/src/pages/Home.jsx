import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppState } from '../state/StateContext'; 
import './Home.css';

export default function HomePage() {
    // const HomePage = () => {
    const navigate = useNavigate();
    const { state } = useAppState();

    // const handleGetStarted = () => {
    //     if (state.token) {
    //     navigate('/upload');
    //     } else {
    //     navigate('/login');
    //     }
    // };

    const handleGetStarted = () => {navigate('/upload')};

    return (
        <div className="homepage">
        {/* Hero Section */}
        <section className="hero">
            <div className="hero-content">
            <h1>Legal Redline Sandbox</h1>
            <p className="hero-subtitle">
                AI-Powered Contract Analysis & Clause Rewriting
            </p>
            <p className="hero-description">
                Transform your legal document review process with our intelligent AI tool that identifies risks, suggests balanced rewrites, and generates comprehensive reports.
            </p>
            <div className="hero-buttons">
                <button 
                className="btn-primary"
                onClick={handleGetStarted}
                >
                Get Started
                </button>
                <button className="btn-secondary">View Demo</button>
            </div>
            </div>
            <div className="hero-visual">
            <div className="visual-placeholder">
                <div className="document-preview">
                <div className="document-header"></div>
                <div className="document-content">
                    <div className="clause original"></div>
                    <div className="arrow-down"></div>
                    <div className="clause improved"></div>
                </div>
                </div>
            </div>
            </div>
        </section>

        {/* Who Are Our Users Section */}
        <section className="section users-section">
            <div className="container">
            <h2>Who Can Benefit From Legal Redline Sandbox?</h2>
            <div className="users-grid">
                <div className="user-card">
                <div className="user-icon">🏢</div>
                <h3>Small Business Owners</h3>
                <p>Review contracts without expensive legal fees. Understand risks in agreements before signing.</p>
                </div>
                <div className="user-card">
                <div className="user-icon">⚖️</div>
                <h3>Legal Professionals</h3>
                <p>Accelerate document review, identify risks faster, and get AI-powered suggestions for improvements.</p>
                </div>
                <div className="user-card">
                <div className="user-icon">👨‍💼</div>
                <h3>Individuals</h3>
                <p>Understand complex legal documents, rental agreements, and service contracts with ease.</p>
                </div>
                <div className="user-card">
                <div className="user-icon">📊</div>
                <h3>Legal Firms</h3>
                <p>Analyze documents efficiently, maintain consistency, and serve more clients effectively.</p>
                </div>
            </div>
            </div>
        </section>

        {/* Why Choose Us Section */}
        <section className="section why-us-section">
            <div className="container">
            <h2>Why Choose Legal Redline Sandbox?</h2>
            <div className="why-us-content">
                <div className="why-us-text">
                <div className="benefit-item">
                    <h3>Overcoming Traditional Limitations</h3>
                    <p>Traditional legal consultancy is manual, time-consuming, and expensive. Our AI-powered solution eliminates these inherent limitations.</p>
                </div>
                <div className="benefit-item">
                    <h3>Cost Effective</h3>
                    <p>Save up to 80% compared to traditional legal review services. No hourly billing - fixed, transparent pricing.</p>
                </div>
                <div className="benefit-item">
                    <h3>24/7 Availability</h3>
                    <p>Get contract analysis anytime, anywhere. No need to wait for business hours or schedule appointments.</p>
                </div>
                <div className="benefit-item">
                    <h3>Superior Drafting Quality</h3>
                    <p>Our AI provides balanced, legally sound rewrites that protect your interests while maintaining fairness.</p>
                </div>
                </div>
                <div className="why-us-visual">
                <div className="comparison-chart">
                    <div className="chart-item traditional">
                    <h4>Traditional Legal Review</h4>
                    <div className="chart-bar">
                        <div className="bar-fill" style={{width: '90%'}}></div>
                    </div>
                    <ul>
                        <li>High Cost</li>
                        <li>Time Consuming</li>
                        <li>Limited Availability</li>
                    </ul>
                    </div>
                    <div className="chart-item our-solution">
                    <h4>Our AI Solution</h4>
                    <div className="chart-bar">
                        <div className="bar-fill" style={{width: '30%'}}></div>
                    </div>
                    <ul>
                        <li>Cost Effective</li>
                        <li>Instant Results</li>
                        <li>24/7 Availability</li>
                    </ul>
                    </div>
                </div>
                </div>
            </div>
            </div>
        </section>

        {/* Privacy & Security Section */}
        <section className="section privacy-section">
            <div className="container">
            <h2>Your Data Security Is Our Priority</h2>
            <div className="privacy-content">
                <div className="privacy-features">
                <div className="privacy-item">
                    <div className="privacy-icon">🔒</div>
                    <div>
                    <h3>End-to-End Encryption</h3>
                    <p>All your documents and data are encrypted both in transit and at rest.</p>
                    </div>
                </div>
                <div className="privacy-item">
                    <div className="privacy-icon">🚫</div>
                    <div>
                    <h3>No Data Retention</h3>
                    <p>We don't store your documents after processing. Your data is deleted immediately.</p>
                    </div>
                </div>
                <div className="privacy-item">
                    <div className="privacy-icon">🔐</div>
                    <div>
                    <h3>Secure Processing</h3>
                    <p>All analysis happens in secure, isolated environments with strict access controls.</p>
                    </div>
                </div>
                <div className="privacy-item">
                    <div className="privacy-icon">📋</div>
                    <div>
                    <h3>Compliance</h3>
                    <p>Our systems comply with data protection regulations to ensure your privacy.</p>
                    </div>
                </div>
                </div>
                <div className="privacy-visual">
                <div className="security-shield">
                    <div className="shield-icon">🛡️</div>
                    <p>Your Documents Are Safe With Us</p>
                </div>
                </div>
            </div>
            </div>
        </section>

        {/* Mission & Vision Section */}
        <section className="section mission-section">
            <div className="container">
            <div className="mission-content">
                <div className="mission-card">
                <h2>Our Mission</h2>
                <p>To democratize access to legal expertise by making contract analysis affordable, accessible, and understandable for everyone, regardless of their legal knowledge or financial resources.</p>
                </div>
                <div className="mission-card">
                <h2>Our Vision</h2>
                <p>To create a world where no one signs a contract they don't fully understand, and where legal protection is accessible to all businesses and individuals.</p>
                </div>
            </div>
            </div>
        </section>

        {/* Features Section */}
        <section className="section features-section">
            <div className="container">
            <h2>Powerful Features</h2>
            <div className="features-grid">
                <div className="feature-card">
                <div className="feature-icon">🔍</div>
                <h3>Risk Identification</h3>
                <p>AI-powered analysis to identify potentially risky clauses and unfavorable terms in your contracts.</p>
                </div>
                <div className="feature-card">
                <div className="feature-icon">✍️</div>
                <h3>Smart Rewriting</h3>
                <p>Get balanced, legally sound alternative language for problematic clauses with explanations.</p>
                </div>
                <div className="feature-card">
                <div className="feature-icon">📊</div>
                <h3>Visual Diffs</h3>
                <p>Clear side-by-side comparisons showing original vs. suggested changes with highlighted differences.</p>
                </div>
                <div className="feature-card">
                <div className="feature-icon">📋</div>
                <h3>Comprehensive Reports</h3>
                <p>Detailed analysis reports with risk scores, explanations, and recommendations for each clause.</p>
                </div>
                <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3>Fast Processing</h3>
                <p>Get results in minutes, not days. Upload your document and receive analysis almost instantly.</p>
                </div>
                <div className="feature-card">
                <div className="feature-icon">💬</div>
                <h3>Plain Language Explanations</h3>
                <p>Understand complex legal terms with simple, clear explanations of what they mean for you.</p>
                </div>
            </div>
            </div>
        </section>

        {/* Facts Section */}
        <section className="section facts-section">
            <div className="container">
            <h2>Legal Document Facts</h2>
            <div className="facts-grid">
                <div className="fact-item">
                <div className="fact-number">70%</div>
                <div className="fact-text">of small businesses encounter legal issues from poorly drafted contracts annually</div>
                </div>
                <div className="fact-item">
                <div className="fact-number">85%</div>
                <div className="fact-text">of people admit to signing contracts they don't fully understand</div>
                </div>
                <div className="fact-item">
                <div className="fact-number">$150B</div>
                <div className="fact-text">is lost by businesses each year due to poor contract management</div>
                </div>
                <div className="fact-item">
                <div className="fact-number">40%</div>
                <div className="fact-text">reduction in legal disputes when contracts are properly reviewed and negotiated</div>
                </div>
            </div>
            </div>
        </section>

        {/* CTA Section */}
        <section className="section cta-section">
            <div className="container">
            <h2>Ready to Transform Your Contract Review Process?</h2>
            <p>Join thousands of users who trust Legal Redline Sandbox for their document analysis needs.</p>
            <div className="cta-buttons">
                <button 
                className="btn-primary"
                onClick={handleGetStarted}
                >
                Start Analyzing Now
                </button>
                <button className="btn-outline">Schedule a Demo</button>
            </div>
            </div>
        </section>
        </div>
    );
}