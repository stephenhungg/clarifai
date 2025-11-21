'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { FileText, Clock, Search } from 'lucide-react';
import { Navigation } from '../components/navigation';
import { StatusBadge } from '../components/status-badge';

interface PaperItem {
  id: string;
  title: string;
  authors: string[];
  uploaded_at: string;
  status: 'uploaded' | 'analyzing' | 'analyzed' | 'error';
  concept_count?: number;
  video_count?: number;
}

export default function PapersPage() {
  const [papers, setPapers] = useState<PaperItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPapers = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/papers`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch papers');
        }
        
        const data = await response.json();
        const papersData = data.papers || [];
        
        // Map backend response to frontend format
        // Backend returns: analysis_status ("pending", "processing", "completed", "failed")
        // Frontend expects: status ("uploaded", "analyzing", "analyzed", "error")
        const statusMap: Record<string, 'uploaded' | 'analyzing' | 'analyzed' | 'error'> = {
          'pending': 'uploaded',
          'processing': 'analyzing',
          'completed': 'analyzed',
          'failed': 'error',
        };
        
        const mappedPapers: PaperItem[] = papersData.map((paper: any) => ({
          id: paper.id,
          title: paper.title || 'Untitled Paper',
          authors: paper.authors || [],
          uploaded_at: paper.upload_time ? new Date(paper.upload_time).toISOString() : new Date().toISOString(),
          status: statusMap[paper.analysis_status] || 'uploaded',
          concept_count: paper.concepts_count,
          video_count: paper.has_video ? 1 : 0,
        }));
        
        setPapers(mappedPapers);
        setError(null);
      } catch (err) {
        console.error('Failed to load papers:', err);
        setError('Failed to load papers. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    loadPapers();
  }, []);

  const filteredPapers = papers.filter((paper) =>
    paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    paper.authors.some((author) => author.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-bg-primary text-text-primary">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 left-0 h-[28rem] w-[28rem] rounded-full bg-white/10 blur-[140px] opacity-45 animate-float" />
        <div
          className="absolute -bottom-32 right-0 h-[32rem] w-[32rem] rounded-full bg-white/5 blur-[180px] opacity-40 animate-float"
          style={{ animationDelay: '1.2s' }}
        />
      </div>

      <Navigation />

      <main className="relative z-10 pt-32 pb-20 px-6">
        <div className="mx-auto max-w-6xl space-y-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-3"
          >
            <p className="text-sm uppercase tracking-[0.4em] text-text-tertiary">Library</p>
            <h1 className="text-[clamp(2rem,4vw,3.5rem)] font-light leading-tight tracking-[-0.03em]">
              Monochrome archive of your analyzed papers.
            </h1>
            <p className="text-text-secondary">
              Search, revisit, and relaunch concept extraction or video generation.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="relative"
          >
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-text-tertiary" />
            <input
              type="text"
              placeholder="Search by title or author"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-2xl border border-white/15 bg-white/5 pl-14 pr-4 py-3 text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-white/20 backdrop-blur-xl transition"
            />
          </motion.div>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-2xl border border-accent-error/40 bg-accent-error/10 px-4 py-3 text-accent-error backdrop-blur-xl"
            >
              {error}
            </motion.div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-white/15 border-t-white" />
            </div>
          ) : filteredPapers.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="glass-panel text-center py-12"
            >
              <FileText className="mx-auto mb-4 h-16 w-16 text-text-tertiary" />
              <h3 className="text-2xl font-light mb-2">Nothing here yet</h3>
              <p className="text-text-secondary mb-6">
                {searchQuery ? 'No papers match your query.' : 'Upload a paper to start your collection.'}
              </p>
              {!searchQuery && (
                <Link href="/" className="btn-primary inline-flex">
                  Upload Paper
                </Link>
              )}
            </motion.div>
          ) : (
            <div className="space-y-4">
              {filteredPapers.map((paper, index) => (
                <motion.div
                  key={paper.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                >
                  <Link href={`/papers/${paper.id}`}>
                    <div className="card card-hover cursor-pointer p-6">
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-3 mb-2">
                            <h2 className="text-2xl font-light tracking-tight">
                              {paper.title || 'Untitled Paper'}
                            </h2>
                            <StatusBadge status={paper.status} size="sm" />
                          </div>
                          {paper.authors && paper.authors.length > 0 && (
                            <p className="text-text-secondary text-sm mb-4">
                              {paper.authors.join(', ')}
                            </p>
                          )}
                          <div className="flex flex-wrap items-center gap-6 text-sm text-text-tertiary">
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4" />
                              <span>{formatDate(paper.uploaded_at)}</span>
                            </div>
                            {paper.concept_count !== undefined && (
                              <span>{paper.concept_count} concepts</span>
                            )}
                            {paper.video_count !== undefined && (
                              <span>{paper.video_count} videos</span>
                            )}
                          </div>
                        </div>
                        <div className="text-text-tertiary">
                          <svg
                            className="h-6 w-6"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5l7 7-7 7"
                            />
                          </svg>
                        </div>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
