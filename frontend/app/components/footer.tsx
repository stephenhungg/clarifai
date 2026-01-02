'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <motion.footer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="relative z-10 border-t border-white/10 bg-black/20 backdrop-blur-2xl"
    >
      <div className="mx-auto max-w-7xl px-6 py-8 md:py-12">
        <div className="grid gap-8 md:grid-cols-4 md:gap-12">
          {/* Brand */}
          <div className="space-y-4">
            <Link href="/" className="text-xl font-light tracking-tight text-white">
              ClarifAI
            </Link>
            <p className="text-sm text-text-secondary">
              AI-powered research assistant for research intuition.
            </p>
          </div>

          {/* Links */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-white">Navigation</h3>
            <nav className="flex flex-col space-y-2">
              <Link
                href="/"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Upload
              </Link>
              <Link
                href="/papers"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Library
              </Link>
            </nav>
          </div>

          {/* Info */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-white">About</h3>
            <nav className="flex flex-col space-y-2">
              <span className="text-sm text-text-secondary">
                Concept distillation
              </span>
              <span className="text-sm text-text-secondary">
                Video synthesis
              </span>
              <span className="text-sm text-text-secondary">
                Code generation
              </span>
            </nav>
          </div>

          {/* Copyright */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-white">Legal</h3>
            <p className="text-xs text-text-tertiary">
              © {currentYear} ClarifAI. All rights reserved.
            </p>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 border-t border-white/5 pt-6 md:mt-12">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <p className="text-xs text-text-tertiary">
              Built by{' '}
              <a
                href="https://github.com/stephenhungg"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-secondary hover:text-white transition-colors underline-offset-4 hover:underline"
              >
                Stephen Hung
              </a>
              {', '}
              <a
                href="https://github.com/qtzx06"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-secondary hover:text-white transition-colors underline-offset-4 hover:underline"
              >
                Joshua Lin
              </a>
              {', and '}
              <a
                href="https://github.com/philip-chen6"
                target="_blank"
                rel="noopener noreferrer"
                className="text-text-secondary hover:text-white transition-colors underline-offset-4 hover:underline"
              >
                Philip Chen
              </a>
            </p>
            <div className="flex items-center gap-6">
              <span className="text-xs text-text-tertiary">
                Powered by Gemini
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.footer>
  );
}

