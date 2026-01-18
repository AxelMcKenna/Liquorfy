import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const BlackBullLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#1f2937" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized bull head */}
      <circle cx="12" cy="12" r="6" fill={color} />
      {/* Horns */}
      <path
        d="M8 8C6 6 4 6 3 7C3 7 4 8 5 8C6 8 7 9 7 9L8 8Z"
        fill={color}
      />
      <path
        d="M16 8C18 6 20 6 21 7C21 7 20 8 19 8C18 8 17 9 17 9L16 8Z"
        fill={color}
      />
      {/* Eyes */}
      <circle cx="10" cy="11" r="1" fill="white" />
      <circle cx="14" cy="11" r="1" fill="white" />
      {/* Nose ring */}
      <circle cx="12" cy="14" r="1.5" stroke="white" strokeWidth="1" fill="none" />
    </svg>
  );
};

export default React.memo(BlackBullLogo);
