tailwind.config = {
  theme: {
    screens: {
      'sm': '480px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px',
    },
    extend: {
      colors: {
        // Fondos y superficies
        surface:        'rgb(var(--surface) / <alpha-value>)',
        'surface-dim':  'rgb(var(--surface-dim) / <alpha-value>)',
        'surface-raised': 'rgb(var(--surface-raised) / <alpha-value>)',
        'surface-overlay': 'rgb(var(--surface-overlay) / <alpha-value>)',
        // Primario (Obsidiana)
        primary:        'rgb(var(--primary) / <alpha-value>)',
        'primary-subtle': 'rgb(var(--primary-subtle) / <alpha-value>)',
        'primary-muted': 'rgb(var(--primary-muted) / <alpha-value>)',
        'primary-ghost': 'rgb(var(--primary-ghost) / <alpha-value>)',
        'primary-faint': 'rgb(var(--primary-faint) / <alpha-value>)',
        // Acento (Rojo Maya)
        accent:         'rgb(var(--accent) / <alpha-value>)',
        'accent-hover':  'rgb(var(--accent-hover) / <alpha-value>)',
        'accent-active': 'rgb(var(--accent-active) / <alpha-value>)',
        'accent-faint':  'rgb(var(--accent-faint) / <alpha-value>)',
        'accent-muted':  'rgb(var(--accent-muted) / <alpha-value>)',
        // Secundario (Azul Maya)
        secondary:      'rgb(var(--secondary) / <alpha-value>)',
        'secondary-subtle': 'rgb(var(--secondary-subtle) / <alpha-value>)',
        'secondary-faint': 'rgb(var(--secondary-faint) / <alpha-value>)',
        // Semánticos
        success:        'rgb(var(--success) / <alpha-value>)',
        'success-faint': 'rgb(var(--success-faint) / <alpha-value>)',
        warning:        'rgb(var(--warning) / <alpha-value>)',
        'warning-subtle': 'rgb(var(--warning-subtle) / <alpha-value>)',
        'warning-faint': 'rgb(var(--warning-faint) / <alpha-value>)',
        // Bordes
        'border-subtle': 'rgb(var(--border-subtle) / <alpha-value>)',
        'border-default': 'rgb(var(--border-default) / <alpha-value>)',
        'border-strong':  'rgb(var(--border-strong) / <alpha-value>)',
        'border-focus':   'rgb(var(--border-focus) / <alpha-value>)',
        // Texto
        'text-primary':   'rgb(var(--primary) / <alpha-value>)',
        'text-secondary': 'rgb(var(--text-secondary) / <alpha-value>)',
        'text-tertiary':  'rgb(var(--text-tertiary) / <alpha-value>)',
      },
      fontFamily: {
        heading: ['"Science Gothic"', 'sans-serif'],
        sans:    ['"Montserrat"', 'sans-serif'],
      },
      borderRadius: {
        'xs': '2px', 'sm': '4px', DEFAULT: '8px',
        'md': '12px', 'lg': '16px', 'xl': '24px', 'full': '9999px',
      },
      maxWidth: {
        '8xl': '1920px',
      }
    }
  }
}
