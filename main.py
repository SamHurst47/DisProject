from app.pipeline import Pipeline
from app.input_modules import TextInputModule
from app.output_modules import PrintOutputModule
from app.static_modules import Static1


def main():
    # 1. Create fixed input
    input_module = TextInputModule("Hello world")

    # 2. Create fixed output
    output_module = PrintOutputModule()

    # 3. Create pipeline
    pipeline = Pipeline(
        input_module=input_module,
        output_module=output_module
    )

    # 4. Add middle (dynamic) modules
    pipeline.add_module(Static1())

    # 5. Run pipeline
    pipeline.run()


if __name__ == "__main__":
    main()
