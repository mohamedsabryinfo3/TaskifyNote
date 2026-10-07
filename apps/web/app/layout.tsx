import './globals.css'
import type { ReactNode } from 'react'
export const metadata={title:'TaskifyNote',description:'Personal AI productivity workspace'}
export default function RootLayout({children}:{children:ReactNode}){return <html lang="en"><body>{children}</body></html>}
