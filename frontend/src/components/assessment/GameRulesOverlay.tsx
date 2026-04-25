import React from 'react';

interface GameRulesOverlayProps {
  title: string;
  tag: string;
  rules: string[];
  onStart: () => void;
}

export const GameRulesOverlay: React.FC<GameRulesOverlayProps> = ({
  title,
  tag,
  rules,
  onStart,
}) => {
  return (
    <div className="neo-brutalist neo-brutalist-layout" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="neo-brutalist-card" style={{ maxWidth: '600px', width: '100%' }}>
        <div className="neo-brutalist-tag" style={{ alignSelf: 'flex-start', marginBottom: '16px' }}>{tag}</div>
        <h1 className="neo-brutalist-title" style={{ marginBottom: '24px' }}>{title}</h1>
        
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ marginBottom: '16px' }}>HOW TO PLAY:</h3>
          <ul style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
            {rules.map((rule, i) => (
              <li key={i}>{rule}</li>
            ))}
          </ul>
        </div>

        <button 
          className="neo-brutalist-button neo-brutalist-button--primary"
          style={{ width: '100%', fontSize: '20px', padding: '20px' }}
          onClick={onStart}
        >
          START GAME
        </button>
      </div>
    </div>
  );
};
