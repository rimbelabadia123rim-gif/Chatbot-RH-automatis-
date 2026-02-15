// Simple SVG upload icon for use in the chatbot interface
export default function UploadIcon({ size = 24, color = '#3b82f6', style = {} }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={style}
    >
      <path
        d="M12 16V4M12 4L7 9M12 4L17 9"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <rect
        x="4"
        y="16"
        width="16"
        height="4"
        rx="2"
        fill={color}
        fillOpacity="0.1"
      />
    </svg>
  );
}
