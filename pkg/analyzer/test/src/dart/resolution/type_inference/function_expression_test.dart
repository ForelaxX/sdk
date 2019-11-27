// Copyright (c) 2019, the Dart project authors. Please see the AUTHORS file
// for details. All rights reserved. Use of this source code is governed by a
// BSD-style license that can be found in the LICENSE file.

import 'package:analyzer/dart/analysis/features.dart';
import 'package:analyzer/src/generated/engine.dart';
import 'package:test_reflective_loader/test_reflective_loader.dart';

import '../driver_resolution.dart';

main() {
  defineReflectiveSuite(() {
    defineReflectiveTests(FunctionExpressionTest);
    defineReflectiveTests(FunctionExpressionWithNnbdTest);
  });
}

@reflectiveTest
class FunctionExpressionTest extends DriverResolutionTest {
  test_returnType_notNullable() async {
    await resolveTestCode('''
var v = (bool b) {
  if (b) return 0;
  return 1.2;
};
''');
    var element = findNode.functionExpression('(bool').declaredElement;
    assertElementTypeString(element.returnType, 'num');
  }

  test_returnType_null_hasReturn() async {
    await resolveTestCode('''
var v = (bool b) {
  if (b) return;
};
''');
    var element = findNode.functionExpression('(bool').declaredElement;
    assertElementTypeString(element.returnType, 'Null');
  }

  test_returnType_null_noReturn() async {
    await resolveTestCode('''
var v = () {};
''');
    var element = findNode.functionExpression('() {}').declaredElement;
    assertElementTypeString(element.returnType, 'Null');
  }

  test_returnType_nullable() async {
    await resolveTestCode('''
var v = (bool b) {
  if (b) return 0;
};
''');
    var element = findNode.functionExpression('(bool').declaredElement;
    if (typeToStringWithNullability) {
      assertElementTypeString(element.returnType, 'int?');
    } else {
      assertElementTypeString(element.returnType, 'int');
    }
  }
}

@reflectiveTest
class FunctionExpressionWithNnbdTest extends FunctionExpressionTest {
  @override
  AnalysisOptionsImpl get analysisOptions => AnalysisOptionsImpl()
    ..contextFeatures = new FeatureSet.forTesting(
        sdkVersion: '2.6.0', additionalFeatures: [Feature.non_nullable]);

  @override
  bool get typeToStringWithNullability => true;
}
