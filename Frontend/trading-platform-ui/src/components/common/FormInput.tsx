import React from 'react';

interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const FormInput: React.FC<FormInputProps> = ({ 
  label, 
  error, 
  className = '', 
  ...props 
}) => {
  return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {label && (
          <label style={{ fontSize: '13px', fontWeight: '500', color: '#374151', minWidth: '130px' }}>
            {label}
          </label>
        )}
        <input
          style={{
            padding: '6px 10px',
            border: '1px solid #d1d5db',
            borderRadius: '4px',
            fontSize: '13px',
            outline: 'none',
            width: '140px'
          }}
          {...props}
        />
        {error && (
          <p style={{ marginLeft: '6px', fontSize: '12px', color: '#ef4444' }}>{error}</p>
        )}
      </div>
    );
};