import type { Metadata, Viewport } from 'next';
import './globals.css';
import './mujheky.css';
import './workspace.css';
export const metadata: Metadata = {title:'MUJheky · Your semester, in the know',description:'Background monitoring for MUJ marks and grades. Know when something changes.',manifest:'/manifest.webmanifest'};
export const viewport: Viewport = {themeColor:'#cec6ba'};
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>}
