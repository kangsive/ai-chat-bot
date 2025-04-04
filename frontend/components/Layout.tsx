import React, { ReactNode } from 'react';
import Head from 'next/head';

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ 
  children, 
  title = 'AI Chatbot' 
}) => {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <Head>
        <title>{title}</title>
        <meta charSet="utf-8" />
        <meta name="viewport" content="initial-scale=1.0, width=device-width" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <main className="flex-grow">
        {children}
      </main>
      
      <footer className="bg-white shadow-md py-4 text-center text-gray-500 text-sm">
        <div className="container mx-auto">
          © {new Date().getFullYear()} AI Chatbot
        </div>
      </footer>
    </div>
  );
};

export default Layout; 