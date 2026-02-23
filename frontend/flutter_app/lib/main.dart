import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'api_service.dart';
import 'home_screen.dart';
import 'voice_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Local backend: use 127.0.0.1 when app runs on same machine (Chrome, Windows).
  // For Android emulator use: http://10.0.2.2:8000
  const baseUrl = String.fromEnvironment('API_BASE_URL',
      defaultValue: 'http://127.0.0.1:8000');
  runApp(const MyApp(baseUrl: baseUrl));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key, required this.baseUrl});

  final String baseUrl;

  @override
  Widget build(BuildContext context) {
    final api = ApiService(baseUrl: baseUrl);
    final voice = VoiceService();

    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => AppState(api: api, voice: voice)..refresh(),
        ),
      ],
      child: MaterialApp(
        title: 'Shopping Assistant',
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFF2D6A4F),
            brightness: Brightness.light,
          ),
          scaffoldBackgroundColor: const Color(0xFFF4F6F8),
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xFF2D6A4F),
            foregroundColor: Colors.white,
            elevation: 4,
            centerTitle: true,
          ),
          cardTheme: CardThemeData(
            elevation: 3,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
          ),
        ),
        home: const HomeScreen(),
      ),
    );
  }
}
