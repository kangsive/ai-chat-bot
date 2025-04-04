import React from 'react';
import Link from 'next/link';
import Layout from '../components/Layout';

const HomePage: React.FC = () => {
  return (
    <Layout title="AI Chatbot - Home">
      <div className="bg-gradient-to-r from-primary-500 to-primary-700 text-white">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:py-24 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
              AI Chatbot
            </h1>
            <p className="mt-6 text-xl max-w-2xl mx-auto">
              A powerful AI chatbot powered by state-of-the-art language models.
              Chat about anything, get answers, and explore the capabilities of AI.
            </p>
            <div className="mt-10 flex justify-center gap-4">
              <Link href="/login" legacyBehavior>
                <a className="px-8 py-3 border border-transparent text-base font-medium rounded-md text-primary-700 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10">
                  Log In
                </a>
              </Link>
              <Link href="/register" legacyBehavior>
                <a className="px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-800 hover:bg-primary-900 md:py-4 md:text-lg md:px-10">
                  Sign Up
                </a>
              </Link>
            </div>
          </div>
        </div>
      </div>
      
      <div className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-primary-600 font-semibold tracking-wide uppercase">Features</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
              A better way to chat with AI
            </p>
          </div>

          <div className="mt-10">
            <div className="space-y-10 md:space-y-0 md:grid md:grid-cols-3 md:gap-x-8 md:gap-y-10">
              <div className="text-center">
                <h3 className="mt-2 text-xl leading-7 font-semibold text-gray-900">
                  Intelligent Conversations
                </h3>
                <p className="mt-3 text-base text-gray-500">
                  Engage in natural conversations with our advanced AI that understands context and provides helpful responses.
                </p>
              </div>

              <div className="text-center">
                <h3 className="mt-2 text-xl leading-7 font-semibold text-gray-900">
                  Secure & Private
                </h3>
                <p className="mt-3 text-base text-gray-500">
                  Your conversations are securely stored and your privacy is always protected.
                </p>
              </div>

              <div className="text-center">
                <h3 className="mt-2 text-xl leading-7 font-semibold text-gray-900">
                  Personalized Experience
                </h3>
                <p className="mt-3 text-base text-gray-500">
                  The more you chat, the better it gets at understanding your preferences and needs.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default HomePage; 