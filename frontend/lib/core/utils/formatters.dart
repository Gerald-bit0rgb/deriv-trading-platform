import 'package:intl/intl.dart';

/// Shared formatting helpers used throughout the app.
class Fmt {
  Fmt._();

  static final _currency = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  static final _compact  = NumberFormat.compact();
  static final _pct      = NumberFormat('0.00%');
  static final _date     = DateFormat('dd MMM yyyy');
  static final _datetime = DateFormat('dd MMM yyyy HH:mm');
  static final _time     = DateFormat('HH:mm:ss');

  static String money(double? v)  => v == null ? '—' : _currency.format(v);
  static String compact(double v) => _compact.format(v);
  static String pct(double v)     => _pct.format(v / 100);
  static String date(DateTime? d) => d == null ? '—' : _date.format(d.toLocal());
  static String datetime(DateTime? d) => d == null ? '—' : _datetime.format(d.toLocal());
  static String time(DateTime? d) => d == null ? '—' : _time.format(d.toLocal());

  /// Returns "+1.23" or "-1.23" with colour hint.
  static String signedMoney(double? v) {
    if (v == null) return '—';
    final s = _currency.format(v.abs());
    return v >= 0 ? '+$s' : '-$s';
  }

  static String confidence(double c) => '${(c * 100).toStringAsFixed(0)}%';
}
