import 'package:freezed_annotation/freezed_annotation.dart';

part 'risk_settings_model.freezed.dart';
part 'risk_settings_model.g.dart';

@freezed
class RiskSettingsModel with _$RiskSettingsModel {
  const factory RiskSettingsModel({
    @Default(0) int id,
    @Default(0) int userId,
    @Default(1.0) double defaultStake,
    @Default(10.0) double maxStake,
    @Default(50.0) double maxDailyLoss,
    @Default(20) int maxDailyTrades,
    @Default(100.0) double dailyProfitTarget,
    @Default(3) int maxOpenTrades,
    @Default(0.85) double takeProfitPct,
    @Default(1.0) double stopLossPct,
    @Default(false) bool trailingStopEnabled,
    @Default(0.1) double trailingStopPct,
    @Default(20.0) double maxDrawdownPct,
    @Default(false) bool emergencyStop,
    @Default(true) bool tradingEnabled,
    @Default(0.65) double minAiConfidence,
  }) = _RiskSettingsModel;

  factory RiskSettingsModel.fromJson(Map<String, dynamic> json) =>
      _$RiskSettingsModelFromJson(json);
}
