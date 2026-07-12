// Simple user model — no code generation needed
class UserModel {
  final int id;
  final String email;
  final String username;
  final String? fullName;
  final bool isActive;
  final bool isVerified;
  final bool hasDerivToken;
  final String? derivAccountId;
  final DateTime? createdAt;

  const UserModel({
    required this.id,
    required this.email,
    required this.username,
    this.fullName,
    this.isActive = true,
    this.isVerified = false,
    this.hasDerivToken = false,
    this.derivAccountId,
    this.createdAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as int? ?? 0,
      email: json['email'] as String? ?? '',
      username: json['username'] as String? ?? '',
      fullName: json['full_name'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      isVerified: json['is_verified'] as bool? ?? false,
      hasDerivToken: json['has_deriv_token'] as bool? ?? false,
      derivAccountId: json['deriv_account_id'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'username': username,
        'full_name': fullName,
        'is_active': isActive,
        'is_verified': isVerified,
        'has_deriv_token': hasDerivToken,
        'deriv_account_id': derivAccountId,
        'created_at': createdAt?.toIso8601String(),
      };

  UserModel copyWith({
    int? id,
    String? email,
    String? username,
    String? fullName,
    bool? isActive,
    bool? isVerified,
    bool? hasDerivToken,
    String? derivAccountId,
    DateTime? createdAt,
  }) {
    return UserModel(
      id: id ?? this.id,
      email: email ?? this.email,
      username: username ?? this.username,
      fullName: fullName ?? this.fullName,
      isActive: isActive ?? this.isActive,
      isVerified: isVerified ?? this.isVerified,
      hasDerivToken: hasDerivToken ?? this.hasDerivToken,
      derivAccountId: derivAccountId ?? this.derivAccountId,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}

class AuthResponse {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final UserModel user;

  const AuthResponse({
    required this.accessToken,
    required this.refreshToken,
    this.tokenType = 'bearer',
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      accessToken: json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
      tokenType: json['token_type'] as String? ?? 'bearer',
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}
