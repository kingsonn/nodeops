/**
 * Navigation Bar Component
 * 
 * Future implementation:
 * - Navigation links
 * - Wallet connection button
 * - User menu
 */

export default function Navbar() {
  return (
    <nav className="bg-slate-800 border-b border-slate-700">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-white">AutoDeFi.AI</h1>
          <div className="text-sm text-slate-400">Wallet connection coming soon</div>
        </div>
      </div>
    </nav>
  )
}
