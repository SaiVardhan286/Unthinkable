import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'models.dart';

/// Convert ImmutableMap and nested structures to regular Map
dynamic _convertToMutable(dynamic value) {
  if (value is Map) {
    return Map<String, dynamic>.from(
      value.map((k, v) => MapEntry(k.toString(), _convertToMutable(v))),
    );
  } else if (value is List) {
    return value.map(_convertToMutable).toList();
  }
  return value;
}

class ApiService {
  ApiService({required this.baseUrl});

  final String baseUrl;

  Uri _u(String path) => Uri.parse('$baseUrl$path');

  Future<List<ShoppingItem>> getItems() async {
    try {
      final resp = await http.get(_u('/items'));
      if (resp.statusCode < 200 || resp.statusCode >= 300) {
        throw Exception('Failed to load items (${resp.statusCode})');
      }
      final decoded = jsonDecode(resp.body);
      final mutable = _convertToMutable(decoded) as List<dynamic>;
      return mutable.map((e) => ShoppingItem.fromJson(e as Map<String, dynamic>)).toList();
    } on SocketException {
      throw Exception('Offline or server unreachable');
    }
  }

  Future<List<ShoppingItem>> modifyItem({
    required String item,
    required int quantity,
  }) async {
    try {
      final resp = await http.post(
        _u('/modify-item'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'item': item, 'quantity': quantity}),
      );
      if (resp.statusCode < 200 || resp.statusCode >= 300) {
        throw Exception(_extractError(resp.body, resp.statusCode));
      }
      final decoded = jsonDecode(resp.body);
      final mutable = _convertToMutable(decoded) as List<dynamic>;
      return mutable.map((e) => ShoppingItem.fromJson(e as Map<String, dynamic>)).toList();
    } on SocketException {
      throw Exception('Offline or server unreachable');
    }
  }

  Future<ProcessVoiceResponse> processVoice({
    required String text,
    String? language,
  }) async {
    try {
      final resp = await http.post(
        _u('/process-voice'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'text': text, 'language': language}),
      );
      if (resp.statusCode < 200 || resp.statusCode >= 300) {
        throw Exception(_extractError(resp.body, resp.statusCode));
      }
      final decoded = jsonDecode(resp.body);
      final mutable = _convertToMutable(decoded) as Map<String, dynamic>;
      return ProcessVoiceResponse.fromJson(mutable);
    } on SocketException {
      throw Exception('Offline or server unreachable');
    } catch (e) {
      throw Exception('Failed to parse response: $e');
    }
  }

  String _extractError(String body, int status) {
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map<String, dynamic>) {
        if (decoded['message'] != null && decoded['error_code'] != null) {
          return decoded['message'].toString();
        }
        if (decoded['detail'] != null) {
          return decoded['detail'].toString();
        }
      }
    } catch (_) {}
    return 'Request failed ($status)';
  }
}

