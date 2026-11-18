#include <iostream>
#include <string>
#include <vector>
#include <filesystem>
#include <fstream>

using namespace std;
namespace fs = std::filesystem;


// ==========================================
// Vehicle Record Class
// ==========================================

class VehicleRecord
{
private:
    string vehicleName;
    int count;

public:
    VehicleRecord(string name, int total)
    {
        vehicleName = name;
        count = total;
    }

    void display()
    {
        cout << vehicleName << " : " << count << endl;
    }
};


// ==========================================
// Abstract Base Class
// ==========================================

class DatasetProcessor
{
protected:
    string datasetName;

public:
    DatasetProcessor(string name)
    {
        datasetName = name;
    }

    virtual void processDataset() = 0;

    virtual ~DatasetProcessor()
    {
    }
};


// ==========================================
// Vehicle Dataset Processor
// ==========================================

class VehicleDatasetProcessor : public DatasetProcessor
{
private:
    string sourcePath;

    vector<string> vehicleClasses =
    {
        "Ambulance",
        "Bus",
        "Car",
        "Motorcycle",
        "Truck"
    };

    vector<int> vehicleCounts =
    {
        0, 0, 0, 0, 0
    };

    vector<VehicleRecord> records;


public:

    VehicleDatasetProcessor(string name, string path)
        : DatasetProcessor(name)
    {
        sourcePath = path;
    }


    // ==========================================
    // Count Images
    // ==========================================

    int countImages()
    {
        int imageCount = 0;

        for (const auto& file :
             fs::recursive_directory_iterator(sourcePath))
        {
            if (file.is_regular_file())
            {
                string extension =
                    file.path().extension().string();

                if (extension == ".jpg" ||
                    extension == ".jpeg" ||
                    extension == ".png")
                {
                    imageCount++;
                }
            }
        }

        return imageCount;
    }


    // ==========================================
    // Count Vehicle Classes
    // ==========================================

    void countVehicleClasses()
    {
        string folders[] =
        {
            "train",
            "valid",
            "test"
        };

        for (const string& folder : folders)
        {
            string labelsPath =
                sourcePath + "/" + folder + "/labels";

            if (!fs::exists(labelsPath))
            {
                continue;
            }

            for (const auto& file :
                 fs::directory_iterator(labelsPath))
            {
                if (!file.is_regular_file() ||
                    file.path().extension() != ".txt")
                {
                    continue;
                }

                ifstream labelFile(file.path());

                int classID;

                while (labelFile >> classID)
                {
                    if (classID >= 0 &&
                        classID < static_cast<int>(vehicleClasses.size()))
                    {
                        vehicleCounts[classID]++;
                    }

                    float x, y, width, height;

                    labelFile >>
                        x >>
                        y >>
                        width >>
                        height;
                }
            }
        }
    }


    // ==========================================
    // Display Statistics
    // ==========================================

    void displayVehicleStatistics()
    {
        records.clear();

        for (int i = 0;
             i < static_cast<int>(vehicleClasses.size());
             i++)
        {
            records.push_back(
                VehicleRecord(
                    vehicleClasses[i],
                    vehicleCounts[i]
                )
            );
        }

        cout << endl;
        cout << "Vehicle Class Statistics" << endl;
        cout << "------------------------------" << endl;

        for (auto& record : records)
        {
            record.display();
        }
    }


    // ==========================================
    // Create YOLO YAML File
    // ==========================================

    void createVehicleYaml()
    {
        ofstream yamlFile("ai/vehicle_data.yaml");

        if (!yamlFile)
        {
            cout << "Error creating vehicle_data.yaml!" << endl;
            return;
        }

        yamlFile << "path: ../dataset_multi/vehicle_yolo\n\n";

        yamlFile << "train: train/images\n";
        yamlFile << "val: valid/images\n";
        yamlFile << "test: test/images\n\n";

        yamlFile << "names:\n";

        for (int i = 0;
             i < static_cast<int>(vehicleClasses.size());
             i++)
        {
            yamlFile << "  "
                     << i
                     << ": "
                     << vehicleClasses[i]
                     << "\n";
        }

        yamlFile.close();

        cout << endl;
        cout << "YOLO configuration created successfully!" << endl;
        cout << "File: ai/vehicle_data.yaml" << endl;
    }


    // ==========================================
    // Process Dataset
    // ==========================================

    void processDataset() override
    {
        cout << "==============================" << endl;
        cout << "   VEHICLE DATASET ANALYSIS" << endl;
        cout << "==============================" << endl;

        cout << "Dataset Name : "
             << datasetName << endl;

        cout << "Source Path  : "
             << sourcePath << endl;

        if (!fs::exists(sourcePath))
        {
            cout << "Dataset folder not found!" << endl;
            return;
        }

        int imageCount = countImages();

        cout << "Total Images : "
             << imageCount << endl;

        countVehicleClasses();

        displayVehicleStatistics();

        createVehicleYaml();

        cout << "==============================" << endl;
    }
};


// ==========================================
// Main Function
// ==========================================

int main()
{
    VehicleDatasetProcessor vehicleDataset(
        "Vehicle Dataset",
        "dataset_multi/vehicle_yolo"
    );

    vehicleDataset.processDataset();

    return 0;
}