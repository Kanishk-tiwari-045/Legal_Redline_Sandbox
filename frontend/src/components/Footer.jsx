import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="bg-gradient-to-b from-gray-800 to-gray-900 text-white py-12 mt-auto border-t border-gray-700">
      <div className="container mx-auto px-4">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
          {/* Brand Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">⚖️</span>
              <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                Legal AI
              </h3>
            </div>
            <p className="text-gray-400 leading-relaxed">
              Empowering legal professionals with AI-driven document analysis and insights.
            </p>
            <div className="flex space-x-4">
              <a href="https://twitter.com" className="text-gray-400 hover:text-blue-400 transition-colors">
                <span className="text-xl">𝕏</span>
              </a>
              <a href="https://linkedin.com" className="text-gray-400 hover:text-blue-400 transition-colors">
                <span className="text-xl">👥</span>
              </a>
              <a href="https://github.com" className="text-gray-400 hover:text-blue-400 transition-colors">
                <span className="text-xl">📦</span>
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-gray-100">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-2">
                  <span>📄</span> Upload Document
                </Link>
              </li>
              <li>
                <Link to="/risk" className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-2">
                  <span>⚠️</span> Risk Analysis
                </Link>
              </li>
              <li>
                <Link to="/chatbot" className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-2">
                  <span>🤖</span> AI Chat
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-2">
                  <span>🔒</span> Privacy Check
                </Link>
              </li>
            </ul>
          </div>

          {/* Features */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-gray-100">Features</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/sandbox" className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-2">
                  <span>✏️</span> Clause Editor
                </Link>
              </li>
              <li>
                <Link to="/explainer" className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-2">
                  <span>💡</span> Legal Explainer
                </Link>
              </li>
              <li>
                <Link to="/export" className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-2">
                  <span>📊</span> Export Reports
                </Link>
              </li>
              <li>
                <Link to="/diff" className="text-gray-400 hover:text-blue-400 transition-colors flex items-center gap-2">
                  <span>🔄</span> Compare Changes
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-gray-100">Contact Us</h4>
            <ul className="space-y-3">
              <li className="flex items-center gap-2 text-gray-400">
                <span>📧</span>
                <a href="mailto:contact@legalai.com" className="hover:text-blue-400 transition-colors">
                  contact@legalai.com
                </a>
              </li>
              <li className="flex items-center gap-2 text-gray-400">
                <span>🌐</span>
                <a href="https://legalai.com" className="hover:text-blue-400 transition-colors">
                  www.legalai.com
                </a>
              </li>
              <li className="flex items-center gap-2 text-gray-400">
                <span>📞</span>
                <span>+1 (555) 123-4567</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-700 pt-8 mt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-gray-400 text-sm">
              © {new Date().getFullYear()} Legal AI. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm">
              <a href="/privacy-policy" className="text-gray-400 hover:text-blue-400 transition-colors">
                Privacy Policy
              </a>
              <a href="/terms" className="text-gray-400 hover:text-blue-400 transition-colors">
                Terms of Service
              </a>
              <a href="/cookies" className="text-gray-400 hover:text-blue-400 transition-colors">
                Cookie Policy
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;