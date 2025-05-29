// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:frontend/main.dart';

void main() {
  testWidgets('Split-view UI skeleton renders all key widgets', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());

    // Check for Product URL input
    expect(find.byKey(const Key('urlInput')), findsOneWidget);
    // Check for Creative Prompt input
    expect(find.byKey(const Key('promptInput')), findsOneWidget);
    // Check for Media Upload button
    expect(find.byKey(const Key('mediaUploadButton')), findsOneWidget);
    // Check for Storyboard Editor
    expect(find.byKey(const Key('storyboardEditor')), findsOneWidget);
    // Check for Generate button
    expect(find.byKey(const Key('generateButton')), findsOneWidget);
    // Check for Render Video button
    expect(find.byKey(const Key('renderButton')), findsOneWidget);
    // Check for Video Output placeholder
    expect(find.byKey(const Key('videoOutputPlaceholder')), findsOneWidget);
  });
}
