'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

export function Navigation() {
  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.19, 1, 0.22, 1] }}
      className="fixed top-0 left-0 right-0 z-50 pointer-events-none"
    >
      <div className="mx-auto mt-6 max-w-6xl px-6">
        <div className="pointer-events-auto flex items-center justify-between rounded-3xl border border-white/10 bg-white/5 px-6 py-4 backdrop-blur-3xl shadow-glow">
          <Link
            href="/"
            className="text-lg font-semibold tracking-tight text-white transition-colors hover:text-text-secondary"
          >
            ClarifAI
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/papers"
              className="px-4 py-2 text-sm text-text-secondary hover:text-white transition-colors"
            >
              Library
            </Link>
            <Link href="/" className="btn-primary text-sm">
              Upload Paper
            </Link>
          </div>
        </div>
      </div>
    </motion.nav>
  );
}
