import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const CountdownLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#22c55e" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized "W" for Woolworths/Countdown */}
      <path
        d="M3 4L6 16L9 8L12 16L15 4H17L13 20H11L9 12L7 20H5L1 4H3Z M17 4L21 16L23 12V20H21V16L19 20H17L15 12L17 4Z"
        fill={color}
      />
      {/* Apple symbol */}
      <circle cx="19" cy="6" r="2" fill={color} />
    </svg>
  );
};

export default React.memo(CountdownLogo);
