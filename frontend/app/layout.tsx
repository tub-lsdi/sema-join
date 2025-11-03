import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SEMA-JOIN: Joining Semantically-Related Tables',
  description: 'A tool for performing joins on semantically related tables',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
