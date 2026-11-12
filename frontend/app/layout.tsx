import type { Metadata, Viewport } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'MUJ Pulse · Your academics, in the loop',description:'Background monitoring for MUJ marks and grades. Know when something changes.',manifest:'/manifest.webmanifest'};
export const viewport: Viewport = {themeColor:'#142a25'};
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>}
