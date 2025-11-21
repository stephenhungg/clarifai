'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Upload } from 'lucide-react';
import { Navigation } from './components/navigation';
import { uploadPaper } from './lib/api';

export default function Home() {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const pdfFile = files.find((file) => file.type === 'application/pdf');

    if (!pdfFile) {
      setError('Please upload a PDF file');
      return;
    }

    await handleUpload(pdfFile);
  }, []);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      return;
    }

    await handleUpload(file);
  }, []);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);

    try {
      const paper = await uploadPaper(file);
      console.log('Upload successful, redirecting to:', `/papers/${paper.id}`);
      router.push(`/papers/${paper.id}`);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload paper. Please try again.');
      setIsUploading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-bg-primary text-text-primary">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-56 right-0 h-[32rem] w-[32rem] rounded-full bg-white/10 blur-[140px] opacity-60 animate-float" />
        <div
          className="absolute bottom-0 left-[-10rem] h-[28rem] w-[28rem] rounded-full bg-white/5 blur-[160px] opacity-50 animate-float"
          style={{ animationDelay: '2s' }}
        />
      </div>
      <Navigation />

      <main className="relative z-10 pt-32 pb-20 px-6">
        <div className="mx-auto max-w-4xl space-y-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
            className="text-center space-y-6"
          >
            <p className="text-sm uppercase tracking-[0.4em] text-text-tertiary">ClarifAI Studio</p>
            <h1 className="text-[clamp(2.75rem,6vw,4.75rem)] font-light leading-tight tracking-[-0.04em]">
              Liquid glass interface for <span className="text-white">research intuition</span>.
            </h1>
            <p className="text-text-secondary text-lg">
              Upload a paper, let agents distill it into concepts, videos, and living notebooks.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15, ease: [0.19, 1, 0.22, 1] }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`group relative glass-panel p-14 transition-all duration-300 ${
              isDragging ? 'ring-2 ring-white/40 scale-[0.99]' : 'hover:ring-2 hover:ring-white/15'
            } ${isUploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}`}
          >
            <div className="pointer-events-none absolute inset-0 rounded-[26px] bg-gradient-to-br from-white/20 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-60" />
            <input
              type="file"
              accept="application/pdf"
              onChange={handleFileSelect}
              disabled={isUploading}
              className="absolute inset-0 z-10 h-full w-full opacity-0 cursor-pointer"
            />

            <div className="relative z-20 flex flex-col items-center gap-6 text-center">
              <motion.div
                animate={isDragging ? { scale: 1.12 } : { scale: 1 }}
                transition={{ type: 'spring', stiffness: 260, damping: 18 }}
                className="rounded-full border border-white/10 bg-white/5 p-6 backdrop-blur-xl shadow-inner-glow"
              >
                {isUploading ? (
                  <div className="h-16 w-16 animate-spin rounded-full border-4 border-white/15 border-t-white" />
                ) : (
                  <Upload className="h-16 w-16 text-white/70" />
                )}
              </motion.div>

              <div>
                <p className="text-2xl font-light tracking-tight">
                  {isUploading ? 'Uploading...' : 'Drop your PDF or click to browse'}
                </p>
                <p className="text-text-secondary mt-2">
                  {isUploading
                    ? 'Parsing, segmenting, and preparing your research artifact.'
                    : 'Drag-and-drop or tap to begin. We support comprehensive research PDFs.'}
                </p>
              </div>

              {error && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="rounded-full border border-accent-error/30 bg-accent-error/10 px-4 py-1 text-sm text-accent-error"
                >
                  {error}
                </motion.p>
              )}
            </div>

            {isUploading && (
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: '100%' }}
                transition={{ duration: 2, ease: 'easeOut', repeat: Infinity }}
                className="absolute bottom-0 left-0 h-1 rounded-full bg-gradient-to-r from-white/0 via-white to-white/0"
              />
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: [0.19, 1, 0.22, 1] }}
            className="grid gap-6 md:grid-cols-3"
          >
            {[
              {
                title: 'Concept distillation',
                description: 'LLM agents surface the core mechanisms and claims.',
              },
              {
                title: 'Video synthesis',
                description: 'Glass panels render monochrome animations with live logs.',
              },
              {
                title: 'Code sketches',
                description: 'Pull runnable Python snippets aligned to each concept.',
              },
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.4 + index * 0.1 }}
                className="card card-hover text-left"
              >
                <p className="text-sm uppercase tracking-[0.3em] text-text-tertiary mb-3">
                  {String(index + 1).padStart(2, '0')}
                </p>
                <h3 className="text-xl font-light mb-2">{feature.title}</h3>
                <p className="text-text-secondary text-sm">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
