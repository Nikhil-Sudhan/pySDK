# Red Aerial Systems Dashboard UI

A modern, responsive dashboard interface for Red Aerial Systems account creation and management.

## Features

- **Modern Design**: Clean, professional interface with dark theme and glassmorphism effects
- **Responsive Layout**: Works seamlessly on desktop, tablet, and mobile devices
- **Interactive Steps**: Progress indicator with clickable navigation steps
- **Form Validation**: Real-time validation with error handling
- **Password Toggle**: Show/hide password functionality
- **Google Integration**: Ready for Google OAuth implementation
- **Smooth Animations**: Entrance animations and hover effects

## Files Structure

```
UI/
├── index.html      # Main HTML file
├── styles.css      # CSS styling and responsive design
├── script.js       # JavaScript functionality
└── README.md       # This documentation file
```

## Quick Start

1. Open `index.html` in your web browser
2. The dashboard will load with the account creation form
3. Navigate through different steps using the sidebar
4. Test form validation and interactive features

## Key Components

### Left Sidebar
- **Red Aerial Systems Logo**: Brand identity with tagline
- **Progress Steps**: 5-step workflow navigation
  - Create Your Account (active)
  - Set up your profile
  - Invite Members
  - Upload Documents
  - Complete Sign In
- **Terms and Conditions**: Footer link

### Main Content Area
- **Beautiful Background**: Aerial imagery with overlay effects
- **Account Creation Form**: 
  - Google Sign Up button
  - Name, Email, Password fields
  - Real-time email validation
  - Password confirmation
  - Sign Up button
  - Sign In toggle

## Interactive Features

### Form Validation
- Real-time email format validation
- Password strength requirements
- Password confirmation matching
- Field-specific error messages

### Password Toggle
- Click the eye icon to show/hide passwords
- Works for both password and confirm password fields

### Step Navigation
- Click any step in the sidebar to navigate
- Form content updates based on selected step
- Visual feedback for active step

### Responsive Design
- Mobile-first approach
- Tablet and desktop optimizations
- Touch-friendly interface elements

## Customization

### Colors
The color scheme can be modified in `styles.css`:
- Primary: `#00d4aa` (teal green)
- Accent: `#ff4444` (red)
- Background: Dark gradients
- Text: White/gray variants

### Branding
Update the logo and company name in `index.html`:
- Logo icon (currently using FontAwesome bullseye)
- Company name: "Red Aerial Systems"
- Tagline: "CONNECTED BY THE SKY"

### Background
The aerial background is implemented as an SVG in CSS. You can replace it with:
- Custom images
- Different SVG patterns
- Gradient backgrounds

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (iOS Safari, Chrome Mobile)

## Dependencies

### External CDNs
- Google Fonts (Inter font family)
- FontAwesome 6.0.0 (icons)
- Google Developers logo (for Google sign-up button)

### No Build Process Required
All files are vanilla HTML, CSS, and JavaScript - no compilation needed.

## Future Enhancements

### Planned Features
- Google OAuth integration
- Form submission to backend API
- Multi-step form with different content per step
- File upload functionality
- Member invitation system
- Email verification workflow

### Technical Improvements
- Form data persistence
- Progressive Web App (PWA) features
- Advanced animations
- Accessibility enhancements (ARIA labels)
- Internationalization (i18n)

## Development Notes

### JavaScript Functions
- `togglePassword()`: Show/hide password fields
- `validateForm()`: Comprehensive form validation
- `showSignIn()`: Toggle between sign-up and sign-in
- `nextStep()`: Progress through workflow steps
- Real-time validation listeners

### CSS Architecture
- Mobile-first responsive design
- CSS Grid and Flexbox layouts
- CSS custom properties for easy theming
- Smooth transitions and hover effects
- Glassmorphism design patterns

## License

This UI kit is part of the Red Aerial Systems project. Please refer to the main project license for usage terms. 