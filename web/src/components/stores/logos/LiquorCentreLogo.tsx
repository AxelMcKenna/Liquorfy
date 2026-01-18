import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const LiquorCentreLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#6366f1" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized "LC" monogram */}
      <path
        d="M3 4H5V18H11V20H3V4Z"
        fill={color}
      />
      <path
        d="M21 6C21 4.89543 20.1046 4 19 4H15C13.8954 4 13 4.89543 13 6V18C13 19.1046 13.8954 20 15 20H19C20.1046 20 21 19.1046 21 18H19C19 18 19 18 19 18H15V6H19C19 6 19 6 19 6H21Z"
        fill={color}
      />
    </svg>
  );
};

export default React.memo(LiquorCentreLogo);
