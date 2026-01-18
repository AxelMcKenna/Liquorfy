import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const LiquorlandLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#3b82f6" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized "LL" monogram */}
      <path
        d="M4 4H6V18H12V20H4V4Z"
        fill={color}
      />
      <path
        d="M14 4H16V18H22V20H14V4Z"
        fill={color}
      />
    </svg>
  );
};

export default React.memo(LiquorlandLogo);
