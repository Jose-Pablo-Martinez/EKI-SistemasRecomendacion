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
        surface:        'var(--surface)',
        'surface-dim':  'var(--surface-dim)',
        'surface-raised': 'var(--surface-raised)',
        'surface-overlay': 'var(--surface-overlay)',
        // Primario (Obsidiana)
        primary:        'var(--primary)',
        'primary-subtle': 'var(--primary-subtle)',
        'primary-muted': 'var(--primary-muted)',
        'primary-ghost': 'var(--primary-ghost)',
        'primary-faint': 'var(--primary-faint)',
        // Acento (Rojo Maya)
        accent:         'var(--accent)',
        'accent-hover':  'var(--accent-hover)',
        'accent-active': 'var(--accent-active)',
        'accent-faint':  'var(--accent-faint)',
        'accent-muted':  'var(--accent-muted)',
        // Secundario (Azul Maya)
        secondary:      'var(--secondary)',
        'secondary-subtle': 'var(--secondary-subtle)',
        'secondary-faint': 'var(--secondary-faint)',
        // Semánticos
        success:        'var(--success)',
        'success-faint': 'var(--success-faint)',
        warning:        'var(--warning)',
        'warning-subtle': 'var(--warning-subtle)',
        'warning-faint': 'var(--warning-faint)',
        // Bordes
        'border-subtle': 'var(--border-subtle)',
        'border-default': 'var(--border-default)',
        'border-strong':  'var(--border-strong)',
        'border-focus':   'var(--border-focus)',
        // Texto
        'text-primary':   'var(--primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-tertiary':  'var(--text-tertiary)',
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
