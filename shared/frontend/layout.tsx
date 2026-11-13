import './globals.css';
import type { Metadata } from 'next';
import { ThemeProvider } from '@/components/theme-provider';

declare global {
  interface Window {
    webkitSpeechRecognition: any;
    SpeechRecognition: any;
  }
}

export const metadata: Metadata = {
  title: 'StoryGen — Six-Scene Adventures',
  description: 'Create gentle, illustrated six-scene stories for children from a few keywords.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      {/* System fonts keep builds reproducible without a runtime Google Fonts request. */}
      <body className="font-sans antialiased transition-colors">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
