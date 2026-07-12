// Simple notification model — no code generation needed
class NotificationModel {
  final int id;
  final String type;
  final String title;
  final String body;
  final bool isRead;
  final DateTime? sentAt;

  const NotificationModel({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    this.isRead = false,
    this.sentAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id'] as int? ?? 0,
      type: json['type'] as String? ?? '',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      isRead: json['is_read'] as bool? ?? false,
      sentAt: json['sent_at'] != null
          ? DateTime.tryParse(json['sent_at'] as String)
          : null,
    );
  }
}
