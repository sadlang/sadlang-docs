# التثبيت والتشغيل

تُبنى لغة ص من المصدر باستخدام **CMake** و**LLVM** ومترجم C++17. هذا الدليل يلخّص
خطوات الحصول على المفسّر والمترجم وتشغيل أوّل برنامج.

## المتطلّبات

- مترجم C++17 (MSVC على Windows، أو Clang/GCC على Linux/macOS).
- CMake 3.20 أو أحدث.
- LLVM (للمترجم `sad-build`؛ المفسّر `sad-run` لا يحتاجه).

## البناء

```powershell
# من جذر مستودع لغة ص
cmake -S . -B build                                   # تهيئة أولى
cmake --build build --config Debug --target sad-run   # المفسّر  → sad.exe
cmake --build build --config Debug --target sad-build # المترجم  → sadc
```

> الهدفان: `sad-run` يبني المفسّر، و`sad-build` يبني المترجم. (الأسماء القديمة
> `sad`/`sadc` أُعيدت تسميتها إلى `sad-run`/`sad-build`.)

## التشغيل

شغّل ملفًّا بالمفسّر مباشرةً:

```powershell
.\build\bin\Debug\sad.exe examples\test_simple.ص
```

أو ترجمه إلى تنفيذيّ أصليّ بالمترجم:

```powershell
.\build\bin\Debug\sadc.exe examples\test_simple.ص -o test_simple.exe
.\test_simple.exe
```

## الاختبارات

```powershell
ctest --test-dir build -R Comprehensive   # فعّلها بـ -DBUILD_TESTS=ON عند التهيئة
```

## التالي

انتقل إلى [أوّل برنامج: أهلًا يا عالم](first-program.md) لكتابة وتشغيل أوّل ملفّ `.ص`.
