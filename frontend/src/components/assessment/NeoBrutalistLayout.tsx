import React from 'react';

interface NeoBrutalistLayoutProps {
  title: string;
  tag: string;
  lives: number;
  currentQuestion: number;
  totalQuestions: number;
  score: number;
  onBack?: () => void;
  children: React.ReactNode;
}

export const NeoBrutalistLayout: React.FC<NeoBrutalistLayoutProps> = ({
  title,
  tag,
  lives,
  currentQuestion,
  totalQuestions,
  score,
  onBack,
  children,
}) => {
  return (
    <div className="neo-brutalist neo-brutalist-layout">
      <header className="neo-brutalist-hud">
        <div className="neo-brutalist-hud-section">
          {onBack && (
            <button className="neo-brutalist-button" onClick={onBack} style={{ padding: '8px 16px' }}>
              [ ← BACK ]
            </button>
          )}
          <h1 className="neo-brutalist-title">
            {title} — <span className="neo-brutalist-tag">{tag}</span>
          </h1>
        </div>
        <div className="neo-brutalist-hud-section">
          <div>
            LIVES: {' '}
            {Array.from({ length: 3 }).map((_, i) => (
              <span key={i} style={{ fontSize: '20px' }}>
                {i < lives ? '●' : '○'}
              </span>
            ))}
          </div>
          <div>Q: {currentQuestion}/{totalQuestions}</div>
          <div>SCORE: {score}</div>
        </div>
      </header>
      <main className="neo-brutalist-content">
        {children}
      </main>
    </div>
  );
};
