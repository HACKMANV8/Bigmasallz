import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'SynthAIx - Scalable Synthetic Data Generator',
  description: 'Generate high-quality synthetic data at scale with AI-powered orchestration',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
          <header className="border-b bg-white shadow-sm">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                    <span className="text-white font-bold text-xl">S</span>
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900">SynthAIx</h1>
                    <p className="text-sm text-gray-500">Scalable Synthetic Data Generator</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <a
                    href="/docs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-gray-600 hover:text-primary-600"
                  >
                    Documentation
                  </a>
                  <a
                    href={`${process.env.NEXT_PUBLIC_API_URL}/docs`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-gray-600 hover:text-primary-600"
                  >
                    API Docs
                  </a>
                </div>
              </div>
            </div>
          </header>
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="border-t bg-white mt-12">
            <div className="container mx-auto px-4 py-6 text-center text-sm text-gray-600">
              <p>© 2025 SynthAIx. Built with ❤️ by the SynthAIx Team</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
