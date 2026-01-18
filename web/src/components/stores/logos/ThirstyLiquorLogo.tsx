import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const ThirstyLiquorLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#14b8a6" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized "TL" with droplet for "thirsty" */}
      <path
        d="M9 2H15V4H13V20H11V4H9V2Z"
        fill={color}
      />
      <path
        d="M17 8H19V18H23V20H17V8Z"
        fill={color}
      />
      {/* Water droplet */}
      <path
        d="M6 10C6 10 4 12 4 14C4 15.6569 5.34315 17 7 17C8.65685 17 10 15.6569 10 14C10 12 8 10 8 10L7 8L6 10Z"
        fill={color}
        opacity="0.7"
      />
    </svg>
  );
};

export default React.memo(ThirstyLiquorLogo);
