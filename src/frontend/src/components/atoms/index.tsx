import type {
  ButtonHTMLAttributes,
  HTMLAttributes,
  ReactNode,
} from 'react';
import { useMemo } from 'react';

type ButtonVariant = 'primary' | 'ghost' | 'neutral' | 'danger' | 'success' | 'warning';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant | string;
  icon?: ReactNode;
}

export const Button = ({
  variant = 'primary',
  icon,
  className,
  children,
  ...rest
}: ButtonProps) => {
  const bootstrapVariant = variant === 'ghost' ? 'outline-secondary' : variant === 'neutral' ? 'outline-dark' : String(variant);
  const classes = ['btn', `btn-${bootstrapVariant}`, 'platform-action', className].filter(Boolean).join(' ');
  return (
    <button className={classes} {...rest}>
      {icon ? <span className="btn-icon" aria-hidden="true">{icon}</span> : null}
      <span className="btn-label">{children}</span>
    </button>
  );
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: ButtonVariant | string;
}

export const Badge = ({ variant = 'neutral', className, children, ...rest }: BadgeProps) => {
  const classes = ['platform-badge', `platform-badge-${variant}`, className].filter(Boolean).join(' ');
  return (
    <span className={classes} {...rest}>
      {children}
    </span>
  );
};

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  width?: number | string;
  height?: number | string;
}

export const Skeleton = ({ width, height, style, className, ...rest }: SkeletonProps) => {
  const classes = ['platform-skeleton', className].filter(Boolean).join(' ');
  return (
    <div
      className={classes}
      style={{ width, height, ...style }}
      {...rest}
    />
  );
};

interface JsonViewerProps extends HTMLAttributes<HTMLPreElement> {
  value: unknown;
  collapsed?: boolean;
}

export const JsonViewer = ({ value, collapsed, className, ...rest }: JsonViewerProps) => {
  const text = useMemo(() => {
    try {
      return JSON.stringify(value ?? null, null, 2);
    } catch {
      return String(value);
    }
  }, [value]);

  const classes = ['json-viewer', collapsed ? 'json-viewer-collapsed' : '', className]
    .filter(Boolean)
    .join(' ');

  return (
    <pre className={classes} {...rest}>
      {text}
    </pre>
  );
};
