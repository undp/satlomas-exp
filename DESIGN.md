# Design

## Clases

1. Suelo de Loma Natural
2. Suelo de Loma Artificial
3. Área urbana
4. Suelo desnudo
5. Cultivo
6. Agua

## Entrenamiento y evaluación

Período: un año entero (2018-11 - 2019-11)

### Prueba 1: 3 mosaicos por año

Train:
  * 2018-11 .. 2018-12
  * 2019-03 .. 2019-04
  * 2019-07 .. 2019-08
Test:
  * 2018-12 .. 2019-01
  * 2019-04 .. 2019-05
  * 2019-08 .. 2019-09

### Prueba 2: 6 mosaicos por año

Train:
  * 2018-11 .. 2018-12
  * 2019-01 .. 2019-02
  * 2019-03 .. 2019-04
  * 2019-05 .. 2019-06
  * 2019-07 .. 2019-08
  * 2019-09 .. 2019-10
Test:
  * 2018-12 .. 2019-01
  * 2019-02 .. 2019-03
  * 2019-04 .. 2019-05
  * 2019-06 .. 2019-07
  * 2019-08 .. 2019-09
  * 2019-10 .. 2019-11


## Processes

### Feature extraction

x Clip source images (S2-10m, S2-20m, S1) to training AOI
x Superimpose all 3 images
x Extract extra features (local stats, Haralick, etc.)
x Concatenate all 3 images and extracted extra features

### Train

x Compute statistics
x Sample positions
x Extract samples
x Train classifier

### Predict

- Clip source images (S2-10m, S2-20m, S1) to AOI
- Superimpose all 3 images
- Extract extra features (local stats, Haralick, etc.)
- Concatenate all 3 images and extracted extra features
- Compute statistics
- Predict with trained classifier
