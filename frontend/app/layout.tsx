import './globals.css';
import { Inter } from 'next/font/google';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './components/AuthProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'AI Chatbot',
  description: 'A powerful AI chatbot application',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <div className="min-h-screen bg-gray-100 flex flex-col">
            <main className="flex-grow">{children}</main>
            
            <footer className="bg-white shadow-md py-4 text-center text-gray-500 text-sm">
              <div className="container mx-auto">
                © {new Date().getFullYear()} AI Chatbot
              </div>
            </footer>
            
            <Toaster position="top-right" />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
} 