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
        surface:        '#FDF8F1',  // Arena cálida
        'surface-dim':  '#EFE9DF',  // Roca desgastada
        'surface-raised': '#FFFFFF', // Piedra caliza
        'surface-overlay': '#F7F1E8', // Pergamino
        // Primario (Obsidiana)
        primary:        '#1E1B18',
        'primary-subtle': '#2D2926',
        'primary-muted': '#453E39',
        'primary-ghost': '#6B625C',
        'primary-faint': '#E6E0D9',
        // Acento (Rojo Maya)
        accent:         '#8B3A3A',
        'accent-hover':  '#7A3030',
        'accent-active': '#6A2828',
        'accent-faint':  '#F5E6E6',
        'accent-muted':  '#D4898A',
        // Secundario (Azul Maya)
        secondary:      '#4A6F8A',
        'secondary-subtle': '#7393B3',
        'secondary-faint': '#E8EFF4',
        // Semánticos
        success:        '#3A6B4A',
        'success-faint': '#EBF4ED',
        warning:        '#8A6020',
        'warning-subtle': '#C08A40',
        'warning-faint': '#FBF2E2',
        // Bordes
        'border-subtle': '#EFE9DF',
        'border-default': '#DCD4C8',
        'border-strong':  '#C9BFB7',
        'border-focus':   '#4A6F8A',
        // Texto
        'text-primary':   '#1E1B18',
        'text-secondary': '#4D4540',
        'text-tertiary':  '#7E756F',
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
