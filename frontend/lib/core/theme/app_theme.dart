import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Brand colours
// ─────────────────────────────────────────────────────────────────────────────
class AppColors {
  AppColors._();

  // Primary brand
  static const Color primary    = Color(0xFF6C63FF); // purple
  static const Color primaryDark = Color(0xFF4A43CC);

  // Accent
  static const Color accent     = Color(0xFF00D4AA); // teal

  // Status
  static const Color success    = Color(0xFF22C55E);
  static const Color danger     = Color(0xFFEF4444);
  static const Color warning    = Color(0xFFF59E0B);
  static const Color info       = Color(0xFF3B82F6);

  // Signal colours
  static const Color buyColor   = Color(0xFF22C55E);
  static const Color sellColor  = Color(0xFFEF4444);
  static const Color waitColor  = Color(0xFFF59E0B);

  // Dark backgrounds
  static const Color darkBg        = Color(0xFF0F0F1A);
  static const Color darkCard      = Color(0xFF1A1A2E);
  static const Color darkCardLight = Color(0xFF252540);
  static const Color darkBorder    = Color(0xFF2D2D50);

  // Light backgrounds
  static const Color lightBg        = Color(0xFFF8F9FF);
  static const Color lightCard      = Color(0xFFFFFFFF);
  static const Color lightCardGrey  = Color(0xFFF1F5F9);
  static const Color lightBorder    = Color(0xFFE2E8F0);

  // Text
  static const Color textLight  = Color(0xFFF8FAFC);
  static const Color textMuted  = Color(0xFF94A3B8);
  static const Color textDark   = Color(0xFF1E293B);
}

// ─────────────────────────────────────────────────────────────────────────────
// Theme builder
// ─────────────────────────────────────────────────────────────────────────────
class AppTheme {
  AppTheme._();

  static ThemeData get dark => _buildTheme(Brightness.dark);
  static ThemeData get light => _buildTheme(Brightness.light);

  static ThemeData _buildTheme(Brightness brightness) {
    final isDark = brightness == Brightness.dark;

    final colorScheme = ColorScheme(
      brightness: brightness,
      primary: AppColors.primary,
      onPrimary: Colors.white,
      secondary: AppColors.accent,
      onSecondary: Colors.white,
      error: AppColors.danger,
      onError: Colors.white,
      surface: isDark ? AppColors.darkCard : AppColors.lightCard,
      onSurface: isDark ? AppColors.textLight : AppColors.textDark,
    );

    final textTheme = GoogleFonts.interTextTheme(
      isDark
          ? ThemeData.dark().textTheme
          : ThemeData.light().textTheme,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      textTheme: textTheme,
      scaffoldBackgroundColor: isDark ? AppColors.darkBg : AppColors.lightBg,

      // AppBar
      appBarTheme: AppBarTheme(
        backgroundColor: isDark ? AppColors.darkCard : AppColors.lightCard,
        foregroundColor: isDark ? AppColors.textLight : AppColors.textDark,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.inter(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: isDark ? AppColors.textLight : AppColors.textDark,
        ),
      ),

      // Cards
      cardTheme: CardTheme(
        color: isDark ? AppColors.darkCard : AppColors.lightCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
            width: 1,
          ),
        ),
        margin: const EdgeInsets.symmetric(horizontal: 0, vertical: 6),
      ),

      // Elevated button
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: GoogleFonts.inter(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
          elevation: 0,
        ),
      ),

      // Outlined button
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primary,
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          side: const BorderSide(color: AppColors.primary),
          textStyle: GoogleFonts.inter(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),

      // Input fields
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: isDark ? AppColors.darkCardLight : AppColors.lightCardGrey,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(
            color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
          ),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.danger),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        labelStyle: TextStyle(
          color: isDark ? AppColors.textMuted : Colors.grey.shade600,
        ),
      ),

      // Bottom nav
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: isDark ? AppColors.darkCard : AppColors.lightCard,
        indicatorColor: AppColors.primary.withOpacity(0.15),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: AppColors.primary, size: 24);
          }
          return IconThemeData(
            color: isDark ? AppColors.textMuted : Colors.grey.shade500,
            size: 24,
          );
        }),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return GoogleFonts.inter(
            fontSize: 12,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
            color: selected
                ? AppColors.primary
                : (isDark ? AppColors.textMuted : Colors.grey.shade500),
          );
        }),
      ),

      // Divider
      dividerTheme: DividerThemeData(
        color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
        thickness: 1,
        space: 1,
      ),

      // Switch
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((s) =>
            s.contains(WidgetState.selected) ? AppColors.primary : Colors.grey),
        trackColor: WidgetStateProperty.resolveWith((s) =>
            s.contains(WidgetState.selected)
                ? AppColors.primary.withOpacity(0.4)
                : Colors.grey.withOpacity(0.3)),
      ),
    );
  }
}
